# Develop locally

1. Clone the repo
2. Install Poetry (if not already)
3. Install dependancies ```poetry install```
4. Point local IDE to virtual env that poetry has created
5. Publish to TestPyPi ```poetry publish --build -r testpypi```



python3 -m pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple spotify_sync==0.1.1