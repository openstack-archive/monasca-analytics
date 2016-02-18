ifeq (testspec,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  TEST_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TEST_ARGS):;@:)
endif


PYTHON=python

all: test style

test:
	$(PYTHON) -m unittest discover -v

testspec:
	$(PYTHON) -m unittest -v $(TEST_ARGS)

clean:
	find . -type f -name '*.pyc' -exec rm {} +

style:
	find . -type f -name '*.py' -exec pep8 --max-line-length 79 {} +

start:
	bash -c "sleep 5; curl -H \"Content-Type: application/json\" -d '{\"action\": \"start_streaming\"}' http://localhost:3000/" &
	$(PYTHON) run.py -p ~/spark -c ./config/markov_source_config.json -l ./config/logging.json


.PHONY: all test clean style testspec
