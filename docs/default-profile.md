# Default profile

`default` is the public, provider-neutral baseline for coding-agent-setup.

It is always available as the fallback baseline, but it does not make any named deployment profile mandatory. Users may create `personal`, `work`, `redhat`, or any other local profile only when they need a policy different from the baseline.

The default configuration:

- uses configured providers only;
- permits local models;
- refuses unconfigured providers;
- enables the generic FlossWare capabilities;
- uses the Turbo C++ TUI theme;
- stores no credentials.

This makes a fresh installation useful without requiring the user to create a profile first.
