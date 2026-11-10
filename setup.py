from setuptools import find_packages, setup


setup(
    name="honestforecast",
    version="0.5.0",
    description="Evidence gates for auditable forecast changes",
    long_description=(__import__("pathlib").Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="wukexin314-art",
    author_email="wukexin314-art@users.noreply.github.com",
    url="https://github.com/wukexin314-art/HonestForecast",
    project_urls={
        "Source": "https://github.com/wukexin314-art/HonestForecast",
        "Issues": "https://github.com/wukexin314-art/HonestForecast/issues",
    },
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    entry_points={
        "console_scripts": [
            "honestforecast=honestforecast.assessment:main",
            "honestforecast-synthetic=honestforecast.synthetic:main",
            "honestforecast-vintage-audit=honestforecast.vintages:main",
            "honestforecast-dengue-pilot=honestforecast.dengue_case:main",
        ]
    },
)
