# tinfoleak
The most complete open-source tool for Twitter intelligence analysis

### Introduction
** tinfoleak ** is an open-source tool within the OSINT (Open Source Intelligence) and SOCMINT (Social Media Intelligence) disciplines, that automates the extraction of information on Twitter and facilitates subsequent analysis for the generation of intelligence. Taking a user identifier, geographic coordinates or keywords, Tinfoleak analyzes the Twitter timeline to extract great volumes of data and show useful and structured information to the intelligence analyst. 

** infoleak ** is included in several Linux Distros: Kali, CAINE, BlackArch and Buscador. It is currently the most comprehensive open-source tool for intelligence analysis on Twitter.

** tinfoleak ** can extract the following information:
- Account info / User Activity / Protected Accounts
- Source Applications / User Devices / Use Frequency
- Hashtags / Mentions / Likes
- Text Analysis / Words Frequency / Media / Metadata
- Visited Places / Routes / Top Locations
- Social Networks / Digital Identities
- Geolocated Users / Tagged Users
- Followers / Friends
- Lists / Collections
- Conversations

### License
tinfoleak is released under the CC-BY-SA-4.0 license. See the <a href="https://github.com/vaguileradiaz/tinfoleak/blob/master/LICENSE.txt">LICENSE.txt</a> file for additional details.

### Installation
Install Python and dependencies:

```
sudo apt install python-pip python-dev build-essential python2.7-dev python-pyexiv2 python-openssl
sudo pip install --upgrade pip 
sudo pip install --upgrade virtualenv 
sudo pip install --upgrade tweepy
sudo pip install --upgrade pillow
sudo pip install --upgrade exifread
sudo pip install --upgrade jinja2 
sudo pip install --upgrade oauth2
```

### Getting started
<p align="center">
  <img src="https://github.com/vaguileradiaz/tinfoleak/blob/master/doc/images/tinfoleak-noparameters.png" />
</p>
