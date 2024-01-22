# Project Title: CO2 Measurement Analysis with Raspberry Pi

## Introduction
This project is a comprehensive guide and toolkit for measuring CO2 levels using a Raspberry Pi equipped with an SCD30 sensor. It includes scripts for data collection and analysis, as well as notebooks for visualizing the data.

# Preparation

Before you can start collecting data with the SCD30 sensor, you need to set up the hardware and prepare the necessary libraries. This section guides you through this process.

## About the SCD30 Sensor
The SCD30 from Sensirion is a high-precision carbon dioxide sensor capable of measuring CO2 levels, temperature, and humidity. It features:
- Non-dispersive infrared (NDIR) CO2 sensor technology
- Sensitivity range (experimentally tested): 400 ppm to 40,000 ppm
- Accuracy: ±(30 ppm)

## Connecting the SCD30 to Raspberry Pi
To connect the SCD30 sensor to your Raspberry Pi, follow the

1. **Soldering the Connector:**
   - Soldering the connector pins to the SCD30 sensor module is essential. In my case, the sensor did not function properly without a secure solder connection.

2. **Wiring:**
   Clear insctuctions can be found here: [SCD30 Connecting](https://github.com/Sensirion/python-i2c-scd30)
3. **Required libraries:**
   - [adafruit_scd30](https://github.com/adafruit/Adafruit_SCD30)
   - busio
   - pandas
   - board
   - numpy
   - plotly
## Configuring and testing the connection
Enable I2C on your raspberry by running `sudo raspi-config` and enabling I2C.
Ensure that sensor became visible: `i2cdetect -y 1`, you should see slave adress as a hexidecimal number


## Making measurments
For this particular project i included 2 buttons and 3 LEDs to signal measuring and pressing buttons, when window i was closing and opening window to further analyse this data. If you are just want to make it measure:
```python
import adafruit_scd30
import busio
import board

i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
scd = adafruit_scd30.SCD30(i2c)
if scd.data_available:
  print(f"CO2: {scd.CO2},Temperature: {scd.temperature} C, Relative humidity: {scd.relative_humidity}")
```
## Running scipt automatically on plugging raspberry
To create new start-up service create a new file in /etc/systemd/system `scd30.service` with following content:
```bash
[Unit]
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python /path/to/script 
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Enable service: `sudo systemctl enable scd30`
Now everything is configured to run script automatically.

## Goal and Setup Explanation

### Objective
The primary objective of this project was to determine the optimal frequency and duration of ventilation in enclosed spaces to maintain air quality. Specifically, the experiment aimed to understand the dynamics of CO2 levels in a room during and after the act of ventilating.

### Experimental Setup
The experiment was conducted using a Raspberry Pi coupled with an SCD30 sensor to monitor CO2 concentration, temperature, and humidity. The setup was further enhanced by integrating two buttons and corresponding LEDs (green for open, red for closed) to signal when a window was opened or closed. This input allowed for an increase in measurement frequency to capture the immediate changes in CO2 levels post-ventilation.

### Measurement Strategy
Under normal circumstances, measurements were taken every 5 minutes. However, upon activating a button, the Raspberry Pi was programmed to increase the data collection frequency to every 30 seconds to 2 minutes for the following 30 minutes. This adjustment was based on the hypothesis that CO2 levels would decrease non-linearly with dramatic reductions immediately after opening a window (turned out to be a linear trend, more on that later). Each time button is pressed, a comment is being added to the logging file ("opened", "closed").

### Concurrent Data Handling
Given the real-time nature of the experiment and the need for responsive data collection following window adjustments, a multithreading approach was adopted. This allowed for simultaneous data reading, precise time-interval tracking during high-frequency measurement periods, and data logging.

### Location Variability
To ensure that the data was not biased by sensor placement, measurements were conducted in two distinct locations within the room:
1. Near the table and window, where air circulation was expected to be most active.
2. In the opposite corner of the room, a spot anticipated to have more stagnant air.

The analysis of the location-based differences in CO2 levels is available in the Jupyter notebooks located in the `/src` directory.

## Data Analysis

The following plot illustrates the CO2 levels measured away from the window. The green line indicates the timestamp for opening the window, and the red line denotes the timestamp for closing it. The trend observed is remarkably linear, suggesting that linear regression could be a suitable method for interpolation.

![Results of Measuring CO2 Away from the Window](https://github.com/iljamak/co2_measuring/blob/main/img/co2_levels.png)

To determine the optimal frequency for room ventilation, I divided the data into two sets: intervals when the window is closed and when it is open. I also made some minor adjustments, such as removing data points from inadvertent button presses (like the erroneous 'close' signal).

For each interval, I computed a linear regression to model the CO2 concentration's increase or decrease and then plotted these trends. By calculating and comparing the average gradients, I found that the variance among them is minimal, suggesting the results are consistent and reliable within the context of this experiment.

Surprisingly, the measurements for CO2 levels taken near the window and away from it yielded similar results.

When comparing the slopes of the 'open' and 'closed' intervals, we can extract a ratio that indicates the most efficient ventilation pattern. The derived ratio of the open_gradient to the close_gradient is a neat '5'. This ratio seems to be independent of the room's size, making these findings potentially applicable to other environments. This implies that to maintain a stable CO2 concentration, one might ventilate their room every hour for 10 minutes, or every two hours for 20 minutes, and so on.

However, pinpointing the absolute best frequency for ventilation is complex. Factors such as room size, window dimensions, and the temperature differential between the inside and outside play significant roles and thus require a more tailored approach.


## Optimal Ventilation Strategy Calculation

Let's attempt to quantify the best ventilation strategy. A well-ventilated room typically maintains a CO2 level of around 500 ppm, which we'll use as our baseline. For my room, with a volume of 30.24 cubic meters and subtracting 2 m³ for space for furniture, we have a usable volume of 28.24 m³. Science papers suggest, that ability to concentrate and task-solving skills are impacted by concentrations already at the level 1000-1500 ppm.[1](https://ehp.niehs.nih.gov/doi/full/10.1289/ehp.1104789),[2](https://www.nature.com/articles/s41370-018-0055-8),[3](https://www.matec-conferences.org/articles/matecconf/abs/2019/39/matecconf_mse2019_12026/matecconf_mse2019_12026.html) So, lets take 1000 ppm as a max limit.

The average gradient for CO2 increase per minute in a 1 m³ space (a tight fit :)) can be calculated using the experimental gradient adjusted for volume. The resulting value represents the CO2 gradient for a room of 1 m³. 

The calculation would be as follows:
$\text{max hours} = \left( \frac{868.6}{\text{volume}} \right) \times \left( \frac{500}{60} \right)$
Where:
- `max` represents the maximum hours without ventilation to not exceed unhealthy CO2 concentration levels.
- `volume` is the room's volume in cubic meters.

After that you should ventilate your room $\frac{max hours}{5}$ hours.

## Another findings
I noticed, that during sleep with closed windows concentarion of co2 can reach as high as 2000-2500. It's a level, that can cause fatigue,headache and adds up to lack of morning freshness. There is a limited amount of scientific data on this, but [this paper](https://onlinelibrary.wiley.com/doi/10.1111/ina.12748) suggests, that CO2 > 1900 ppm is detrimental for well-being. This concentration is higher, because during sleep metabolical processes are slowing down and don't requite that much of oxygen. 
My room is very small (28 m3 of space only) and during night CO2 is rising above that level, if you have a larger room, that it's not a thing to worry about, but if you room size is comparable to mine, than i suggest to consider sleeping with open window at least part of the night. In my case maximum duration of sleep i can afford until reaching harmful limit is 6.9 hours. If you want to find maximum for youslelf go check 'near window' notebook.
## Additional Findings

During my analysis, I observed that CO2 concentrations can reach as high as 2000-2500 ppm during sleep with closed windows. These levels are potentially concerning, as they can cause symptoms like fatigue, headache, and a lack of morning freshness. While there is limited scientific data on this topic, [a study](https://onlinelibrary.wiley.com/doi/10.1111/ina.12748) suggests that CO2 levels exceeding 1900 ppm can be detrimental to well-being. This heightened concentration at night can be attributed to slower metabolic processes during sleep, which reduce the body's oxygen requirements.

Given that my room is relatively small (only 28 m³), CO2 levels rise above this threshold if the windows are kept closed throughout the night. For those with larger rooms, this may not be a significant concern. However, if your room size is similar to mine, I recommend considering keeping a window open for at least part of the night. In my case, the maximum duration of sleep I can afford before reaching harmful CO2 levels is roughly 6.9 hours. To determine the maximum safe duration for your room, check the 'near window' notebook.


## Colnclusion
In summary, this project involved developing a detailed system utilizing a Raspberry Pi and SCD30 sensor, enhanced with Python libraries such as pandas, numpy, and multithreading, to monitor CO2 levels in indoor spaces. Our main goal was to explore effective CO2 reduction strategies for small, enclosed areas. The insights gained offer valuable tips and straightforward steps for maintaining healthy indoor air quality.
