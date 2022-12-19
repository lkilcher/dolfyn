I haven't figured out how to script this because I don't know how to grab the `<version info>` string. Also, it could be risky to scriptify this. So, follow these steps. The commands below assume you're in the repository root folder. 

First edit the `meta.yaml` file to point to the version of dolfyn that you want to build. You need to point to a PyPi source to avoid git-lfs errors in conda-build. Also, you'll need to replace `<version info>` in the below commands with the appropriate string.

Then run `conda-build . -o build/conda/`

Then run `conda convert build/conda/dolfyn-<version info>-py27*.tar.bz2 -p osx-64,linux-64,linux-32,win-32,win-64`.

Then upload those files:

    anaconda login
    anaconda upload build/conda/**/dolfyn-<version-info>-py27*.tar.bz2
