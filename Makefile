ifeq (testspec,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  TEST_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TEST_ARGS):;@:)
endif

MONANAS_SRC=monasca_analytics
PYTHON=python

all: test style

test:
	$(PYTHON) -m unittest discover -v

testspec:
	$(PYTHON) -m unittest -v $(TEST_ARGS)

clean:
	find $(MONANAS_SRC) -type f -name '*.pyc' -exec rm {} +

style:
	find $(MONANAS_SRC) -type f -name '*.py' -exec pep8 --max-line-length 79 {} +

start:
	bash -c "sleep 7; curl -H \"Content-Type: application/json\" -d '{\"action\": \"start_streaming\"}' http://localhost:3000/" &
	$(PYTHON) run.py -p ~/spark/spark-1.6.1 -c ./config/metric_experiments.json -l ./config/logging.json


.PHONY: all test clean style testspec
