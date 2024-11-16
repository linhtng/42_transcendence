# 🐝 BeePong!

![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=yellow) ![Django REST Framework](https://img.shields.io/badge/Django_REST_Framework-092E20?logo=django&logoColor=white) ![Daphne](https://img.shields.io/badge/Daphne-512BD4?logo=django&logoColor=white)  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white) 

 ![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)  ![OAuth](https://img.shields.io/badge/OAuth-4285F4?logo=oauth&logoColor=white)
![HTTPS](https://img.shields.io/badge/HTTPS-565656?logo=letsencrypt&logoColor=white) ![Docker Compose](https://img.shields.io/badge/Docker_Compose-1DA1F2?logo=docker&logoColor=white)

BeePong, or 42 name `ft_transcendence`, is the last core project we did at Hive Helsinki, presenting a modern reinterpretation of the classic Pong game. Leveraging a robust Django-powered backend and a single page application (SPA) vanilla JavaScript frontend, this project introduces a remote multiplayer experience with real-time interactions and AI opponent. 


## Overview
This group project is about creating a website for the mighty Pong contest! 🏓

![BeePong design vision](BeePong_vision_240615.png)
[Figma](https://www.figma.com/design/42yVXZOi6yLRxybTmu8lhG/BEE-PONG?node-id=0-1&t=JObdYVC2Pk32AxSm-1)

## Key Features and Modules

- **Web Gameplay**: Remote Play functionality with real-time interactions using WebSocket
- **User Management**: Remote authentication using OAuth
- **Server-side Pong Game** : implementing the game logic in the server side, enabling interaction through both a web interface and CLI while offering an
API for easy access to game resources and features

## Modules

- **Web**
	- *Major module*: Use a framework as backend :white_check_mark:
	- *Minor module*: Use a front-end framework or toolkit :white_check_mark:
	- *Minor module*: Use a database for the backend :white_check_mark:
- **User Management**
	- *Major module*: Implementing a remote authentication :white_check_mark:
- **Gameplay and User Experience**
	- *Major module*: Remote players :white_check_mark:

- **AI-Algo**
	- *Major module*: Introduce an AI Opponent :white_check_mark:
   
- **Accessibility**
	- *Minor module*: Expanding Browser Compatibility :white_check_mark:

## Practical details:
- You can choose to either play a single match or in a tournament
- Different players can play on the same computer or from different computers on the same network
- In single match you will play against an AI
- The tournament is a simple single-elimination tournament, the players are randomly matched against each other and the winner of each match continues

## Installation

* Clone this repository:

```shell
https://github.com/linhtng/42_transcendence.git
```
* Go to the project folder:

```shell
cd 42_transcendence
```
* Fill the `.env`-file values as necessary

```Run make
make
```
* On your browser, navigate to `https://localhost:8443` and have fun! (Note: There is a warning generated due to a self-signed certificate)

* To uninstall:

```
make clean_all
```

## Resources
- [Mastering Django: Essential Design Patterns and Best Practices](https://www.linkedin.com/pulse/mastering-django-essential-design-patterns-best-mohammad-fa-alfard-zsg3f/)
- [Django Project Architecture: The best project skeleton ever](https://rajanmandanka.medium.com/django-project-architecture-the-best-project-skeleton-ever-a184143f1c82)
- [How the Django-Docker-Frontend system can be connected](https://medium.com/@bekojix0660/42-ft-transcendence-0d952c94ea05)
- [42 API](https://api.intra.42.fr/apidoc) | Documentation to build an application with 42 API. | `Intra` |
- [PostgreSQL commands and flags](https://hasura.io/blog/top-psql-commands-and-flags-you-need-to-know-postgresql)
- [Website vulnerability concerns 101](https://hacksplaining.com/lessons)

---

This project represents a collaborative effort at Hive Helsinki, embodying the spirit of innovation and the challenge of modern web development. Buzzing into the world of `BeePong` and experience the fun of online Pong gameplay, see who is the queen bee.
