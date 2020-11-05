## Battery optimisation
Simple Dash app to run optimal dispatch of a battery in a power market.

#### Install & run

Clone repository in folder of choice.

Create a virtual environment:
`python3 -m venv .venv/battery-optimisation`

Activate it:
`source .venv/battery-optimisation/bin/activate`

Install requirements:
`pip install -r requirements.txt`

Run app:
`gunicorn app:server`
