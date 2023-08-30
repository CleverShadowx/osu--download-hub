# osu-yoink

Installation
------------

```shell
# install the required modules
pip install -r requirements.txt
```
Usage
------

```python
python main.py --username USERNAME [--top-plays TOP_PLAYS] [--maps-type MAPS_TYPE] [--maps-amount MAPS_AMOUNT] [--output-dir OUTPUT_DIR]
```
Examples
-------
```python
# downloads the beatmaps of the user's top 25 plays
python main.py --username mrekk --top-plays 25

# downloads all of the user's ranked maps
python main.py --username kanui --maps-type ranked --maps-amount 999

```
    
