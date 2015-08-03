## .NET example

This assumes that you have a ``docfx`` executable on your `PATH`.
It also depends on the sphinxcontrib-dotnet domain: https://github.com/rtfd/sphinxcontrib-dotnetdomain

Currently this is setup to build the Indentity repo from ASP.Net

We don't have the checkout in the repo,
but there's a ``clone.sh`` in the ``example`` directory which will clone it properly.


Then you should simply be able to run ``make html`` in this directory.
