// Provides a trivial Python interface to the DLL loader.
// This implementation is not thread safe and is only intended to be used once.

#include "dll_loader.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static DLLContext context;

typedef uint32_t (*ResolveImportByOrdinal)(const char *image, uint32_t ordinal);
typedef uint32_t (*ResolveImportByName)(const char *image, const char *name);

static ResolveImportByOrdinal resolve_import_by_ordinal_proc = NULL;
static ResolveImportByName resolve_import_by_name_proc = NULL;

static bool ResolveImportByOrdinalUnwrapper(const char *image, uint32_t ordinal, uint32_t *result) {
    *result = resolve_import_by_ordinal_proc(image, ordinal);
    return *result != 0;
}

static bool ResolveImportByNameUnwrapper(const char *image, const char *export, uint32_t *result) {
    *result = resolve_import_by_name_proc(image, export);
    return *result != 0;
}

bool LoadDLL(
        const uint8_t *raw_data,
        uint32_t raw_data_size,
        ResolveImportByOrdinal resolve_import_by_ordinal,
        ResolveImportByName resolve_import_by_name) {
    memset(&context, 0, sizeof(context));
    context.input.raw_data = (void*)raw_data;
    context.input.raw_data_size = raw_data_size;

    resolve_import_by_ordinal_proc = resolve_import_by_ordinal;
    resolve_import_by_name_proc = resolve_import_by_name;

    context.input.alloc = malloc;
    context.input.free = free;
    context.input.resolve_import_by_ordinal = ResolveImportByOrdinalUnwrapper;
    context.input.resolve_import_by_name = ResolveImportByNameUnwrapper;

    bool result = DLLParse(&context);
    if (!result) {
        fprintf(stderr, "DLLParse failed: %d:%d\n", context.output.context, context.output.status);
    }
    return result;
}

bool RelocateDLL(uint32_t new_base) {
    return DLLRelocate(&context, new_base);
}

uint8_t *LoadedImage() {
    return context.output.image;
}

uint32_t LoadedImageSize() {
    return context.output.header.OptionalHeader.SizeOfImage;
}

uint32_t LoadedImageEntrypoint() {
    return (uint32_t)(intptr_t)context.output.entrypoint;
}

void FreeDLL() {
    DLLFreeContext(&context, false);
}
