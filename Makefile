.PHONY: all setup clean_dist distro clean install deb_dist upload-packages upload-building upload testsetup test

NAME='rosrelease'
VERSION=`./setup.py --version`

OUTPUT_DIR=deb_dist


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
	scp dist/${NAME}-${VERSION}.tar.gz ros@ftp-osl.osuosl.org:/home/ros/data/download.ros.org/downloads/${NAME}

clean: clean_dist
	echo "clean"

install: distro
	sudo checkinstall python setup.py install

deb_dist:
	python setup.py --command-packages=stdeb.command sdist_dsc --workaround-548392=False bdist_deb

upload-packages: deb_dist
	dput -u -c dput.cf all-shadow-fixed ${OUTPUT_DIR}/${NAME}_${VERSION}-1_amd64.changes 
	dput -u -c dput.cf all-ros ${OUTPUT_DIR}/${NAME}_${VERSION}-1_amd64.changes 

upload-building: deb_dist
	dput -u -c dput.cf all-building ${OUTPUT_DIR}/${NAME}_${VERSION}-1_amd64.changes 

upload: upload-building upload-packages

testsetup:
	echo "running rosrelease-legacy tests"

test: testsetup
	nosetests --with-coverage --cover-package=rospkg --with-xunit
