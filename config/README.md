# Welcome

Welcome to our interactive compute environment! Here you will get a grasp what this environment is all about.

## Ready to get started?

To begin, have a look in the `notebooks` folder in the navigation tree or click [here](./notebooks/00-Getting%20started.ipynb) to quickly launch the first part in the series. To navigate up the tree, hover over the `Name` field on the left to determine the best level to go to.

## Environment Details

### Tree structure

On the left, you will find the navigation tree. The root has been set to the `/home` location of this compute environment and initially, it will show its contents. Aside from this document, there are 3 folders: `common`, `notebooks`, and a third (`<username>`) which should correspond to your user `HOME` directory.

### Persistence and accessibility

For your compute environment, only two directories are persisted: `<username>` and `common`. Therefore, if anything needs to be accessible once your instance powers off, it is best to store it there. The only distinction between `<username>` and `common` is that if you are accessing a host with various compute environments, then `common` will be accessible from each of your environments. Thus, you may use it as a means to transfer documents between them. Also, be aware that inactive server instances will be periodically powered off.

### Available tools

Currently, this compute system provides the following system tools:
- python
- pip
- conda
- git
- mysql-client
- jq
- vim
- inotify-tools

With regard to python/conda packages, the following are preloaded:
- datajoint
- datajoint_connection_hub
- numpy
- pandas
