# Automatic classification of healthy or diseased plants using images
## Master degree thesis project code

### Repository and code description

The code is all created using Google Colab platform. 
For that reason there are available two formats: .ipynb for the jupiter or google colab notebook and .py for python code only.
The flow of the code is created thinking on the possibility of run limited part of that, by executing the wanted colab notebook's cells. So the .py code is all together, and can't be run as is.

The differences between the four notebooks are only for the NN algorithm used, indicated in the name of each file, and for AlexNet_KFold the cross validation method implemented, not present in the other three notebooks.

The first seven sets of cells ("Modules", "Imports", "General constants", "Define drive for save output files", "Import dropbox folder", "Define dataset directory", "Base functions") are in common for all files, and have to be executed each time we start a new runtime in order to define python modules, dataset and basic functions.

After that it's possible to run one of the four following sets, based on the scope of the run:
- "Random Search", for different training and validation based on random hyperparameters' values;
- "Specific Run", for training and validation based on prefixed hyperparameters' values;
- "Grid Search", for training and validation based on combinations of hyperparameters' values extracted from arrayd of possible values;
- "Specific Run for testing", for training and testing based on prefixed hyperparameters' values;

Finally it's possible to run "Flush mounted drive" in order to be sure that the output files are saved on drive mounted directory (this path has to be created before running in own Google Drive. Actually is set as "ColabOutput/Tesi" in code).

### Images
The images are missing in the repository for privacy reason. In every colab note there is a section about downloading the image repository on Dropbox, using the exposed API, but the token is omitted.
