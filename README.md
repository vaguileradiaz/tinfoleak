# tinfoleak
The most complete open-source tool for Twitter intelligence analysis

### Introduction
<p align="justify">
<b>tinfoleak</b> is an open-source tool within the OSINT (Open Source Intelligence) and SOCMINT (Social Media Intelligence) disciplines, that automates the extraction of information on Twitter and facilitates subsequent analysis for the generation of intelligence. Taking a user identifier, geographic coordinates or keywords, <b>tinfoleak</b> analyzes the Twitter timeline to extract great volumes of data and show useful and structured information to the intelligence analyst. 
</p>

<p align="justify">
<b>tinfoleak</b> is included in several Linux Distros: <a href="https://www.kali.org/">Kali</a>, <a href="http://www.caine-live.net/">CAINE</a>, <a href="http://blackarch.org/">BlackArch</a> and <a href="https://inteltechniques.com/buscador/">Buscador</a>. It is currently the most comprehensive open-source tool for intelligence analysis on Twitter.
</p>

<b>tinfoleak</b> can extract the following information:
- Account info / User Activity / Protected Accounts / User Relations
- Source Applications / User Devices / Use Frequency
- Hashtags / Mentions / Likes
- Text Analysis / Words Frequency / Media / Metadata
- User Visited Places / User Routes / User Top Locations
- Social Networks / Digital Identities
- Geolocated Users / Tagged Users
- Followers / Friends
- Lists / Collections
- Conversations

### License
<b>tinfoleak</b> is released under the <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC-BY-SA-4.0</a> license. See the <a href="https://github.com/vaguileradiaz/tinfoleak/blob/master/LICENSE.txt">LICENSE.txt</a> file for additional details.

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
The first time you runs <b>tinfoleak</b>, you need to assign the OAuth settings.

> 1. Edit "tinfoleak.conf" <br>
> Use your favorite editor ;-) 

> 2. Give value to these variables: <br>
> CONSUMER_KEY <br>
> CONSUMER_SECRET <br>
> ACCESS_TOKEN <br>
> ACCESS_TOKEN_SECRET <br>
> - How to obtain these values: <br>
> https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens

> 3. Save "tinfoleak.conf"

> 4. Execute "tinfoleak.py"

<p align="center">
  <img src="https://github.com/vaguileradiaz/tinfoleak/blob/master/doc/images/tinfoleak-ui.png" />
</p>
