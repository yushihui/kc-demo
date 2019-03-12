# Branching & Tagging & Release
* please follow git-flow rules http://confluence.netbraintech.com/confluence/pages/viewpage.action?pageId=72558317
* tagging & release conventions http://confluence.netbraintech.com/confluence/pages/viewpage.action?pageId=75282809
# How to build
### Build
1. Change your source code which under src folder
2. Run command "nbr build", it will build all resource and generate all resources to distribute folder
3. commit & push to git server
4. tagging
5. draft a release
### Examples
* nbr build -s(ource) driver -o folderX----------------### build all drivers and export to folder x
* nbr build -s(ource) driver/xyz -o folderY------------### just build driver xyz to folder y
* nbr build--------------------------------------------### build all resources under current folder
* nbr patch -b(ase) v7.1.0 -head v8.0.0 -o folder------### generate a patch package for upgrade v7.0.0 to v8.0.0
