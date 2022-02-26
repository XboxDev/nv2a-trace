#include <stdio.h>
#include <string.h>
#include <windows.h>

#include "command_processor_util.h"
#include "xbdm.h"

// Command prefix that will be handled by this processor.
// Keep in sync with value in ntrc.py
static const char kHandlerName[] = "ntrc";

static HRESULT_API ProcessCommand(const char *command, char *response,
                                  DWORD response_len,
                                  struct CommandContext *ctx);

HRESULT __declspec(dllexport) DxtMain(void) {
  return DmRegisterCommandProcessor(kHandlerName, ProcessCommand);
}

static HRESULT_API ProcessCommand(const char *command, char *response,
                                  DWORD response_len,
                                  struct CommandContext *ctx) {
  const char *subcommand = command + sizeof(kHandlerName);

  if (!strncmp(subcommand, "hello", 5)) {
    strncpy(response, "Hi from ntrc", response_len);
    return XBOX_S_OK;
  }

  return XBOX_E_UNKNOWN_COMMAND;
}
