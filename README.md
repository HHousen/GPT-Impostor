<img src="GPT%20Impostor%20Logo.png" alt="GPT Impostor Logo" width="200"/>

# GPT Impostor
> Impersonate your friends on Discord using the latest research in AI and machine learning. Originally developed during BigRed//Hacks @ Cornell.

[![GitHub license](https://img.shields.io/github/license/HHousen/GPT-Impostor.svg)](https://github.com/HHousen/GPT-Impostor/blob/master/LICENSE) [![Github commits](https://img.shields.io/github/last-commit/HHousen/GPT-Impostor.svg)](https://github.com/HHousen/GPT-Impostor/commits/master) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub issues](https://img.shields.io/github/issues/HHousen/GPT-Impostor.svg)](https://GitHub.com/HHousen/GPT-Impostor/issues/) [![GitHub pull-requests](https://img.shields.io/github/issues-pr/HHousen/GPT-Impostor.svg)](https://GitHub.com/HHousen/GPT-Impostor/pull/)

**Check out [the website](https://gptimpostor.tech) for more information.**

[![Add the bot to your Discord server!](add-to-discord_button.png)](https://gptimpostor.tech)

## Getting Started (Installation)

You can either run GPT Impostor directly on a computer using Python or run it in a pre-built environment via docker.

### Bare-metal

1. Clone this repo and cd into the directory: `git clone https://github.com/HHousen/GPT-Impostor && cd gpt-impostor`
2. Install Python and Pip. On most linux systems this can be done with `sudo apt install python3 python3-pip`.
3. Create a virtual environment: `python3 -m venv env`
4. Activate virtual environment: `source env/bin/activate`
5. Install dependencies: `pip3 install -r requirements.txt`
6. Make a copy of `.env.example` (`cp .env.example .env`) and change the `BOT_TOKEN` value to your bot's token.
7. Source your environment variables: `source .env`
8. Run the bot: `python3 bot.py`

### Docker

1. Install [Docker](https://docs.docker.com/get-docker/) & [Docker-Compose](https://docs.docker.com/compose/install/).
2. Get the [docker-compose.yml](./docker-compose.yml) file: `wget https://raw.githubusercontent.com/HHousen/GPT-Impostor/master/docker-compose.yml`
3. Replace the `BOT_TOKEN` environment variable in docker-compose.yml with your bot's token.
4. (Optional) Change the volume mapping. The database and log files are located at `/usr/src/app/db_log` within the container. To make sure these files are not erased when the container updates, they are mapped to `/opt/gpt-impostor` on the host system. You can change the location of these files on the host system if desired by modifying the part that reads `/opt/gpt-impostor`.
5. Start the container: `sudo docker-compose up -d gpt-impostor`.

## Meta

[![ForTheBadge built-with-love](https://ForTheBadge.com/images/badges/built-with-love.svg)](https://GitHub.com/HHousen/)

Hayden Housen – [haydenhousen.com](https://haydenhousen.com)

Distributed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) for more information.

<https://github.com/HHousen>

## Contributing

All Pull Requests are greatly welcomed.

Questions? Commends? Issues? Don't hesitate to open an [issue](https://github.com/HHousen/GPT=Impostor/issues/new) and briefly describe what you are experiencing (with any error logs if necessary). Thanks.

1. Fork it (<https://github.com/HHousen/GPT-Impostor/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
