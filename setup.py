setup(
    name="pdf-split",
    version="1.0.1",
    description="Fractionner des PDF",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/egrisel/pdf-split",
    author="Gwap.ch",
    author_email="gwap.websites@gmail.com",
    license="LGPL",
    classifiers=[
        "License :: OSI Approved :: LGPL License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=["pdf_split"],
    include_package_data=True,
    install_requires=[
        # "feedparser", "html2text", "importlib_resources", "typing"
        "PySide2", "PyMuPDF"
    ],
    entry_points={"console_scripts": ["pdf_split=app:main"]},
)
