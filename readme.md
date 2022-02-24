# CRMScript Fetcher

CRMScript Fetcher is a GUI application that can download CRMScripts from your 
SuperOffice installations, and create the scripts as files within a 
folder structure on your local PC.

## About

CRMScript Fetcher is useful for downloading your current scripts into a local repository,
which you then may use for pushing into Github/Gitlab etc. with your preferred git client.

When fetching, it will create the following two folders inside your chosen directory:
- Scripts
- Triggers

Inside these folders, all scripts/triggers will be created as files with a .crmscript file extension.
For Scripts, it will also recreate the exact same folder structure as the one you have in SuperOffice.

## Important to know

The software is provided "as is" without warranty of any kind. 
All responsibility of the usage of CRMSCript Fetcher lies on you.

> :warning: **When fetching, all files and folders within the "Scripts" and "Triggers" folders WILL be 
> deleted if they are not present in SuperOffice.**
> 
> 
> This also includes files/folders that weren't created by CRMScript Fetcher to begin with, so it is not
> advisable to put anything there manually.
> 
> However, files/folders within the root directory will not be deleted, so you can put stuff there safely.

It is also worth noting that, technically, all files and folders within the Scripts and Triggers folders will be deleted and recreated
every time you click fetch, even if you have done no changes in SuperOffice. 

It is up to you to consider if this poses any problems for your usage. 
Based on my own usage, git will not detect these deletes/rewrites as changes.

#### About the temp backup folder
Each fetch will create a "temp" folder where your current local Scripts/Triggers
folders are moved into, as a failsafe in case the fetch fails during its execution.
The temp folder will be deleted again upon completing the fetch, so you shouldn't normally see it.

If something does go wrong, you can move the contents of temp back into the root folder.

Sometimes, the temp folder might not be deleted correctly due to Windows permission
errors. Usually this works itself out by running the fetch again.

## Prerequisites

- A SuperOffice installation with Service and Developer Tools
  - Only tested on Online so far, but should work on an "on premises" installation as well.


- A local PC running Windows
  - Tested on Windows 11 only. Probably works on earlier versions of Windows as well. Just haven't tried it.

## Getting Started

1. Head over to Releases on the right hand side to download. 


2. Unpack the zip file wherever you want

## How to use

1. Open CRMScript Fetcher.crmscript in a text editor, and copy the contents.


2. In your SuperOffice installation, create a new script and paste the contents.
Give it an include name (e.g. "crmscript_fetcher") and a secret key (or just use the one generated).


3. Run CRMScript Fetcher.exe.


4. Click "Add tenant"
   - Tenant name: Friendly name of the installation
   - SuperOffice Service URL: For Online environments this will be something like
https://online.superoffice.com/CustXXXXX/CS
   - Script include ID: Your include name
   - Script key: Your secret key
   - Local directory: Click Browse to pick your directory where the folders will be created.
   

5. Click Save settings


6. Click Fetch CRMScripts to fetch!


All your tenant settings will be saved locally in the tenant_settings.json file.


## Built With

- Python
- CRMScript

## Authors

* **Espen Steen** - [ehs5](https://github.com/ehs5/)

## Acknowledgments
Inspired by:
* [ExpanderSync by Kodesentralen](https://github.com/Kodesentralen/ExpanderSync)