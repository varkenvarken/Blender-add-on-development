<img src="basis.png" width="25%">

# Blender add-on development for beginners

This is the repository that accompanies [the YouTube video series](https://youtube.com/playlist?list=PLxyAbGpHucHZs5InOs_9-apX7wBIQtrrJ&si=kmYMtRvAGMqP9qw0) on writing add-ons for Blender.

It contains [the source code](/add-ons/) for the add-ons that were shown in the videos, as well as for some of of the [snippets](/snippets/)

In order of appearance (click to follow the link to the relevant video, some add-ons are discussed in the same video and some videos present more than one bit of code):

## Introduction video

Release date: **14 january 2026**

[**Video: Blender add-on development**](https://youtu.be/brcuzWr8l_Q)

## Module: Getting started

Release date: **14 january 2026**

### add-ons (click to go to relevant video)
- [move_x.py](https://youtu.be/u65VncJHO4A) [**Video: How to move a cube**](https://youtu.be/u65VncJHO4A)
- [move_x_menu.py](https://youtu.be/GoOwF0faSsM) [**Video: Getting started**](https://youtu.be/GoOwF0faSsM)
- [move_x_poll.py](https://youtu.be/wyq9lSA9BgQ) [**Video: Your first add-on**](https://youtu.be/wyq9lSA9BgQ)
- [move_x_property.py](https://youtu.be/wyq9lSA9BgQ) [**Video: Your first add-on**](https://youtu.be/wyq9lSA9BgQ)
- [About IDEs, no code](https://youtu.be/CshKJ-Pk788) [**Video: external editors**](https://youtu.be/CshKJ-Pk788)

## Module: Adding mesh objects

Release dates: **21 & 28 january 2026**

### add-ons (click to go to relevant video)
- [add_star_basic.py](https://youtu.be/3ufMK24tiXU) [**Video: Adding mesh objects**](https://youtu.be/3ufMK24tiXU)
- [add_star.py](https://youtu.be/kD-K-ljJQf4) [**Video: A mesh from scratch**](https://youtu.be/kD-K-ljJQf4)
- [add_star_with_operators.py](https://youtu.be/vR3-q5BYlRQ) [**Video: A mesh from operators**](https://youtu.be/vR3-q5BYlRQ)
- [add_star_with_modifiers.py](https://youtu.be/DJj4ycpRD9w) [**Video: Adding a modifier**](https://youtu.be/DJj4ycpRD9w)

## Module: Skinning an armature

Release date: **4 february 2026**

### add-ons / snippet (click to go to relevant video)
- [Intro, no code](https://youtu.be/xvwydYy7bII) [**Video: Skinning an armature - Intro**](https://youtu.be/xvwydYy7bII)
- [skin_armature.py](https://youtu.be/hKaWaIYJdMI) [**Video: Skinning an armature - Geometry**](https://youtu.be/hKaWaIYJdMI)
- [skin_armature.py](https://youtu.be/rk5aFsNqCik) [**Video: Skinning an armature - Modifiers**](https://youtu.be/rk5aFsNqCik)
- [change_vertex_radii.py](https://youtu.be/bZWgEG-Xb5k) [**Video: Skinning an armature - Tips**](https://youtu.be/bZWgEG-Xb5k)

## Module: Rigging a curve

Release date: **11 february 2026**

### add-ons (click to go to relevant video)
- [Intro, no code](https://youtu.be/uWCpqOgYIdM) [**Video: Rigging a curve - Intro**](https://youtu.be/uWCpqOgYIdM)
- [rig_curve.py](https://youtu.be/m4s-m9pTUfw) [**Video: Rigging a curve - Code**](https://youtu.be/m4s-m9pTUfw)

## Module: Overlays

Release date: **18 february 2026**

### add-ons / snippet (click to go to relevant video)

- [overlay_cube.py](https://youtu.be/f10SyYoorV8) [**Video: Overlays and preferences - Overlays**](https://youtu.be/f10SyYoorV8)
- [overlay_text.py](https://youtu.be/f10SyYoorV8) [**Video: Overlays and preferences - Overlays**](https://youtu.be/f10SyYoorV8)
- [distance_overlay.py](https://youtu.be/F8DhKTWXl8w) [**Video: Overlays and preferences - The overlay add-on**](https://youtu.be/F8DhKTWXl8w)
- [user preferences in distance_overlay.py](https://youtu.be/F8DhKTWXl8w) [**Video: Overlays and preferences - User preferences**](https://youtu.be/F8DhKTWXl8w)
- [tip to improve distance_overlay.py](https://youtu.be/EUpGNfuUtH8) [**Video: Overlays and preferences - Tips**](https://youtu.be/EUpGNfuUtH8)
  
## Installing the add-ons

In each module we create several versions of the same addon, each time with the same name,
so before installing a new version make sure to check if there already is a version installed
in *Preferences > Add-ons*, and if so, uninstall it.

Then install the add-on by going to Preferences > Add-ons > Install from disk (at the top right corner),
and then locate the add-on to install.

If you are unfamiliar with GitHub, you can either click on the green `Code` button and select `Download Zip` to get all code as one zip file, or you can go to one of the individual files in the [add-ons](/add-ons/) directory and
download one of them by clicking on it and then selecting `Download raw file` (upper right).

If you are familiar with GitHub and git, you can of course choose to clone the repository instead.

> [!NOTE]  
> The repository only contains the final version shown in the videos, but often enhanced with extra comments.

> [!NOTE]
> If you use an IDE like Visual Studio Code, you might want to create a virtual environment and install the [fake-bpy-module](https://pypi.org/project/fake-bpy-module/) from pypi. We discuss that briefly in the [**Video: external editors**](https://youtu.be/CshKJ-Pk788)

## License

All *source code* and *documentation* in this repository is released under a [GPL license](/LICENSE).

The logo is (c) 2025 varkenvarken, All rights reserved.

## Contributions and suggestions

If you have a suggestion for a topic you´d like to see in the series, create an [issue in this repo](https://github.com/varkenvarken/Blender-add-on-development/issues), or add a comment to one of the videos in [the series](https://youtube.com/playlist?list=PLxyAbGpHucHZs5InOs_9-apX7wBIQtrrJ&si=gWrpdnJ7424x7DqL).

<a href="https://ko-fi.com/varkenvarken"><img src="KofiLogo.webp" width="20%">Consider leaving me a tip on Ko-Fi (if you can afford it)</a>
