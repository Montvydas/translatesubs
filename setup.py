import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="translatesubs",
    version="0.0.1",
    license="Apache",
    author="Montvydas Klumbys",
    author_email="motnvydas.klumbys@gmail.com",
    description="It's a tool to translate subtitles into any language, that is supported by google translator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Montvydas/translatesubs",
    download_url="https://github.com/Montvydas/translatesubs/archive/v_0.0.1.tar.gz",
    keywords=["SUBTITLES", "TRANSLATE"],
    packages=setuptools.find_packages(),
    install_requires=[            # I get to this in a second
        'pysubs2',
        'googletrans',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Video Consumption Tools',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'translatesubs=translatesubs.translatesubs:main'
        ]
    },
}
