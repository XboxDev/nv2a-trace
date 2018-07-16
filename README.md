# Warning

This is preliminary software. Don't expect anything to work.
Also see [issues](https://github.com/XboxDev/nv2a-trace/issues).

As this accesses your Xbox hardware directly, it *could* do permanent damage.
Use at your own risk, don't do anything stupid.

It is also known to be unstable and can behave randomly.


## nv2a-trace

nv2a-trace is similar to [apitrace](https://github.com/apitrace/apitrace), but targeting the Xbox GPU instead of desktop graphics APIs.

nv2a-trace runs remotely on a development machine.
It allows you to stop your Xbox GPU command stream and inspect each GPU method before execution.
It uses [xboxpy](https://github.com/XboxDev/xboxpy) to connect to a target Xbox.

nv2a-trace can dump intermediate rendering steps like this:

![Screenshot of Burnout 3](https://i.imgur.com/a2GuIFz.png)

Currently, most output will be send to PNG files in the current folder.
Additionally a "debug.html" will be created which shows the captured commands.
This output format is a temporary solution.
Eventually there'll be one of the following:

* GUI, and tracing and UI will be largely decoupled.
* Parsable output ASCII format which automatically acts as UI.

There is currently no parsable trace-file output, and replaying traces is not possible.


### Usage

This project uses [xboxpy](https://github.com/XboxDev/xboxpy).
Please read its documentation to find out how to configure it for your Xbox.

Afterwards, you can run these commands:

```
git clone https://github.com/XboxDev/nv2a-trace.git
cd nv2a-trace
python3 nv2a-trace.py
```

The last line will run nv2a-trace and connect to your Xbox.
It will automatically start tracing.

**This tool may also (temporarily) corrupt the state of your Xbox.**
If this tool does not work, please retry a couple of times.

---

(c)2018 XboxDev maintainers

All rights reserved.
