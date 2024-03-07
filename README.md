# supervisord-watchdog

A Python package which monitors the state of supervisord processes, and
terminates the container if any of the critical processes terminate,
if any of the processes crash, and optionally if all processes have terminated.

## Usage

In a container which uses supervisord as its init process, make sure the supervisord-watchdog
package is installed.

```
pip install supervisord_watchdog
```

Then, add the following to your `supervisord.conf` file:

```conf
# supervisord_watchdog will kill the container if program:example-proc dies.
[eventlistener:supervisord-watchdog]
command=/usr/local/bin/supervisord_watchdog
    --critical-process example-proc
events=PROCESS_STATE
autostart=true
autorestart=false
startretries=0
```

The available arguments to pass to `supervisord_watchdog` are:

```
usage: supervisord_watchdog [-h] [--termination-grace-period TERMINATION_GRACE_PERIOD] [--critical-process CRITICAL_PROCESS [CRITICAL_PROCESS ...]]
              [--terminate-if-all-processes-end] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Supervisord watchdog

optional arguments:
  -h, --help            show this help message and exit
  --termination-grace-period TERMINATION_GRACE_PERIOD, -t TERMINATION_GRACE_PERIOD
                        The number of seconds to wait for the container to shut down gracefully before sending SIGKILL to all processes. (default: 5.0)
  --critical-process CRITICAL_PROCESS [CRITICAL_PROCESS ...], -c CRITICAL_PROCESS [CRITICAL_PROCESS ...]
                        The names of the critical supervisord processes which should be monitored by the watchdog. If any of these processes terminate, then the container will
                        be terminated (default: [])
  --terminate-if-all-processes-end, -T
                        If this argument is provided, then the container will be terminated if all supervisord processes terminate. (default: False)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The log level to use for the watchdog. (default: INFO)
```

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
