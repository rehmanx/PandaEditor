# PandaEditor is moved to a new repository [Link](https://github.com/barbarian77/PandaEditor) this repository will soon be archived.

## A level editor for Panda3d game engine with bare minimum features to provide an editor centric workflow.

![Image](images//01.png)

#### Current features include
1. Object manipulation
2. Support for runtime user modules 
3. Editor plugin support
4. Properties panel 
5. File browser
6. Console panel

#### Currently PandaEditor is still in alpha stage, a lot of important features are still missing including
* Action manager ( undo / redo system )
* Project management and scene save / reload system
* Some parts of code needs refactoring
* Making editor workflow more intuitive

#### Dependencies
1. WxPython
2. Python Watch dog

#### Install
1. clone / download this repo
2. run main.py

#### Attributions
PandaEditor is using the Gizmos package and InfoPanel from another open source panda3d project [link](https://github.com/Derfies/panda3d-editor).

### Support
## Manual
* [Starting a new project](https://github.com/rehmanx/PandaEditor/blob/main/README.md#starting-a-new-project "")
* [Assets management](https://github.com/rehmanx/PandaEditor/blob/main/README.md#assets-management)
* [Object manipulation](https://github.com/rehmanx/PandaEditor/blob/main/README.md#object-manipulation)
* [Runtime modules](https://github.com/rehmanx/PandaEditor/blob/main/README.md#runtime-user-modules)
* [Editor plugins](https://github.com/rehmanx/PandaEditor/blob/main/README.md#editor-plugins)
* [Other](https://github.com/rehmanx/PandaEditor/blob/main/README.md#other)
* [Known issues](https://github.com/rehmanx/PandaEditor/blob/main/README.md#known-issues)
* [Getting started](https://github.com/rehmanx/PandaEditor/blob/main/README.md#getting-started)

### Starting a new project
When you start PandaEditor a default project with some samples is setup for you.
Its located in current working directory and should not be deleted. You can use default project for any purpose, however to create a new project go to
**_Menubar > Project > Start New Project_** and choose a valid name and path.

### Assets management
* To import assets in your project go to **_Resource browser > Folder > Import Assets_**.
* In PandaEditor you can also append a folder outside of current working project, to append an external folder go to **_Menubar > Project > AppendLibrary_**, editor will start monitoring changes to any appended directory, the appended assets exists in you project like any other imported assets.

### Object manipulation 
* alt + right mouse button to rotate
* alt + middle mouse to dolly
* alt + left mouse button drag to zoom

### Runtime user modules

![Image](images//module.png)

PandaEditor has two states, Editor and Game state. Editor state is for level design, object manipulation, creating user modules and defining behaviors etc. and game state is what you would expect as final game view.  
Runtime user modules are only executed in game state, and any changes made to a user module in game state are reverted as soon as game state is exited, these are used to define behaviors of objects or nodepaths while in game state. 
A user module in PandaEditor is a python file which the editor loads as an asset, however for the editor to consider the python file as PandaEditor's user module,
* The python file should contain a class with same name as of python file.
* Class should inherit from PModBase.

To create a new user module **_Resource Browser > Project > ( select a folder, left click to open context menu ) > Add > UserModule_**.  
To see some example usages of user modules, see samples included with default project.  

### Editor plugins
Editor plugins are executed both in editor and game state. They inherit from PModBase, can be used to create tools and extend editor.  
To see some example usages of editor plugins, see samples included with default project.  

### Other
1. PandaEditor can also load and display .txt files, just import .txt files in your project like any other asset. 
  ![Image](images//text_file.png)

### Known issues
### Getting started
To get started, there are samples included with the default project, a more comprehensive getting started section will soon be created.
