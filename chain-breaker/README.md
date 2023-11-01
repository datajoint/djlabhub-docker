TODO - will make this a proper README.md later

Pro
- Break the chain of dependencies of self-managed base images
  - Reduce image maintenance hell
  - Use jupyter/minimal-notebook as base image instead
- Compatible with previous supported feature as many as possible
- Provide simpler way for mainteners to manage system dependencies and for users to install packages
- Provide a way to config jupyter through environment variables
- This can be used as jupyter lab, so we can archive djlab-docker and only focus on this repo

Con
- Username if jovyan by default, consider this is a minor issue, since it's only visible in the terminal
- Larger image size, this can be optimized when it becomes a problem
