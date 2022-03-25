0) Build a dolfyn development environment.

   - In anaconda you can install dependencies using the `environment.yml` file:

         conda env create -n dolfyn-dev -f environment.yml
      
   - Also be sure to install the repo to this environment in *editable* mode:
     
         conda activate dolfyn-dev  # activate the env
         pip install -e .  # install dolfyn in editable mode

1) Get set up
    - Open an issue (optional)
    - Create a branch
    
2) Create a plan in `todo-branch.md`

3) Make changes to documentation first!
    - The documentation source lives in `docs/`
    - Build the documentation by running `make html` in the `docs/` folder.
    - You can preview the built documentation by directing your browser to `file://<dolfyn-repo-path>/docs/build/html/index.html`
    - Documenting your plans before making changes to the code accomplishes two things:
      i. It makes you think about what you're going to do, and how it will affect the API, before you put time into doing it
      ii. It gives you a big head-start on actually writing the documentation (which, if you're like me, is so easy to overlook/forget)

4) Make changes to the code

5) Test that changes don't break/fail tests (or that failures are consistent with change)

6) Create a test that verifies the change (this should be included in your changes)

7) Make entry for change in `changelog.md`

8) Once finished create a PR (mention issue) and wait for TravisCI + AppVeyor to do checks
