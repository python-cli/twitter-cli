# twitter-cli

> Parse and download the tweets from home timeline, specified user timeline, favorites list.



#### Usage

```shell
➜ twitter-cli
Usage: twitter-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug
  --help                Show this message and exit.

Commands:
  credential  Verify the current user credential.
  favorites   Fetch the user's favorite statuses.
  timeline    Fetch the specified user's timeline.
➜ twitter-cli credential --help
Usage: twitter-cli credential [OPTIONS]

  Verify the current user credential.

Options:
  --help  Show this message and exit.
➜ twitter-cli timeline --help
Usage: twitter-cli timeline [OPTIONS] [USERNAME]

  Fetch the specified user's timeline.

Options:
  --download-media / --no-download-media
  --help                          Show this message and exit.
➜ twitter-cli favorites --help
Usage: twitter-cli favorites [OPTIONS]

  Fetch the user's favorite statuses.

Options:
  --from-latest / --from-last
  --download-media / --no-download-media
  --destroy / --no-destroy
  --help                          Show this message and exit.
➜ 
```



#### Author

[Will Han](https://xingheng.github.io)