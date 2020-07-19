# Fake Chroma Key for Webinars

This is a very simple code to capture a webcam stream, remove its background using [openCV](https://opencv.org/) and export it as a virtual webcam using the [v4l2loopback](https://github.com/umlaeute/v4l2loopback) module using a pipe to [ffmpeg](https://ffmpeg.org/).

Check my video showing the code running on my [youtube channel](https://youtu.be/ly5gwzSZ_MQ). For this video I've added a few openCV windows to show the mask and illustrate the code working, which made the code too heavy and the video has some lags because of this. But showing a single openCV window is not that heavy. In any case, in the next version I'll improve it all a bit, adding an option to hide the screen and simply export to the virtual webcam.

## How does it work?

Once the code is running and streaming the content to a virtual webcam, you can use it as an input to any other program (zoom, skype, [OBS Studio](https://obsproject.com/), etc...).

The algorithm I'm proposing here is very simple:

1. I move away from the camera view and press a key ('c') and it takes a picture of the background;
2. A mask is then set by the absolute difference between the new frame and the initial photo;
3. Apply a threshold to the mask to emphasize the foreground and eliminate some noise
4. Apply a median blur to the mask to eliminate more noise
5. Dilate the mask to further eliminate noise and expand a bit the contour
6. Gaussian blur the mask to make the edges smooth
7. Set the new background (e.g. use green and export to OBS to use as chroma key)

## How to use it

This code only works on Linux and you'll need **python**, **opencv**, **v4l2loopback**, **ffmpeg**.

### Create a virtual webcam using the v4l2loopback module

Please check the [v4l2loopback documentation](https://github.com/umlaeute/v4l2loopback) on how to install it and more details about possible configurations.

I like to name the virtual webcam with a large number (10) to make sure it does not match the notebook (0, and 1 for metadata) or external (2, and 3 for metadata) webcams. To start a virtual video device as `/dev/video10`, run

```bash
$ sudo modprobe v4l2loopback video_nr=10
```

To delete it, simply unload the module

```bash
$ sudo rmmod v4l2loopback
```

### Edit the parameters and run the python script

At the begining of the code you should check some parameters. Particularly `indev` and `outdev` for the input and output devices.

- **indev** refers to the input device, which will be passed to opencv. For instance, if the input webcam is `/dev/video0`, then `indev=0`.
- **outdev** refers to the output device for a virtual webcam. In the **v4l2loopback** example above it would be `/dev/video10`. 

Next run `$ python backsub.py` and the webcam stream will be extracted and piped to the virtual device.

To properly remove the background you need good lighting and you must allow the code to take a picture of the clean background. So, leave the webcam steady and get out of the picture. Press *c* and the code will capture the background. Now you can go back to your seat and the background will be gone.

## To do

The code works well for me as it is. But it would be great if we could improve it by:

- rewrite as a C library to be integrated into [webcamoid](https://webcamoid.github.io/), or as an [OBS Studio](https://obsproject.com/) plugin.
- organize it as a proper python library and cythonize it.
- replace with ffmpeg pipe with a better approach to stream to the virtual device using v4l2 directly.

# Acknowledgements

I would like to thank all involved in the discussion at the [webcamoid github forum](https://github.com/webcamoid/webcamoid/issues/250) for the suggestions. As discussed there, there's a much better code beeing developed: https://grail.cs.washington.edu/projects/background-matting/, but while it is not finished, I'll use mine ;-)



