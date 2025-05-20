Hello! I’m Joshua Barragán. I’ve developed and continue improving this web application that will allow you to view solar graphs according to your position in the world, as well as observe the behavior of temperatures with EPW files.

![image](https://github.com/user-attachments/assets/fdbe7ee6-5f10-463d-9ff3-00fa38ca5f37)

In this code, tables and files will be generated allowing you to visualize the 3D solar chart alongside your architectural model, as well as the various temperature data extracted from the EPW file. This program uses the dry bulb temperature as a reference and applies the adaptive comfort temperature equation.

![image](https://github.com/user-attachments/assets/aca72b33-249d-4d87-bd34-75cd0921fc5b)

Based on this reference, a change in temperature or color in the indicators is considered every 2 to 2.5 degrees Celsius.

![image](https://github.com/user-attachments/assets/82d75cd6-d4c0-4989-a68d-09c74f4d205b)

Finally, the solar chart is constructed in both 3D and 2D by making the appropriate projections and considering a bimonthly average of temperatures to generate the color samples in the 3D chart composed of 6x24 panels. This results in an average hourly temperature for each of the 12 months.

![image](https://github.com/user-attachments/assets/7036916c-7af7-4319-a743-bd72700fd1cf)

Results:

![image](https://github.com/user-attachments/assets/91972808-a8b5-4a7b-9cf1-99c109300ff3)

![image](https://github.com/user-attachments/assets/b0e61e28-57f1-4c54-9d21-0b07d63307ea)

![image](https://github.com/user-attachments/assets/5644cc4b-96ea-495d-ab42-34a1874c5c8c)

![image](https://github.com/user-attachments/assets/ab25d1c8-5cb3-485d-9dc8-08f6069867eb)

USE: 
This page is very simple to use, feel free to play around with it. You just need to clone the repository and run app.py, which will start the page and all its features.
Make sure to have all the Python libraries installed by running the following command: pip install -r requirements.txt

In the templates folder, you’ll find all the HTML and JS that build the graphical part. In static, your solar graph will be stored, and in uploads, 
you can view comfort temperatures and auxiliary CSV files with the important information. 
Additionally, I’ve provided some example files for you to use: EPW for your climate data, and OBJ for your 3D objects.

this code is protected
Copyright (c) Joshua Barragán, August 2024. All rights reserved.
