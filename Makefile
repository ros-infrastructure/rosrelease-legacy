.PHONY: all setup clean_dist distro clean install dsc source_deb upload

NAME='rosrelease'
VERSION=`./setup.py --version`

all:
	echo "noop for debbuild"

setup:
	echo "building version ${VERSION}"

clean_dist:
	-rm -f MANIFEST
	-rm -rf dist
	-rm -rf deb_dist

distro: setup clean_dist
	python setup.py sdist

push: distro
	python setup.py sdist register upload
	scp dist/${NAME}-${VERSION}.tar.gz ipr:/var/www/pr.willowgarage.com/html/downloads/${NAME}

clean: clean_dist
	echo "clean"

install: distro
	sudo checkinstall python setup.py install

testsetup:
	echo "running rosrelease-legacy tests"

test: testsetup
	nosetests --with-coverage --cover-package=rospkg --with-xunit
