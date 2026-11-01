# Security Policy

## GeoToolkit for Google Earth Engine

GeoToolkit is an open-source QGIS plugin designed to retrieve and process geospatial datasets from Google Earth Engine and other supported data providers.

We take security seriously and encourage users and contributors to report potential vulnerabilities responsibly.

## 1. Supported Versions

Security updates will primarily target the latest publicly released version of GeoToolkit.

| Version | Security Support |
|---------|------------------|
| Latest release | Supported |
| Previous releases | Not guaranteed |
| Development versions | Use with caution |

## 2. Reporting a Vulnerability

If you discover a potential security vulnerability in GeoToolkit, please report it responsibly.

Before reporting:
- Do not publicly disclose the vulnerability.
- Avoid sharing sensitive credentials or personal information.
- Provide enough technical information to reproduce the issue safely.

Please use GitHub's private vulnerability reporting feature where available.

Alternatively, contact the project maintainer through the contact information provided in the repository.

**Please do not submit sensitive vulnerability details through public GitHub issues.**

## 3. Authentication and Credentials

GeoToolkit may interact with Google Earth Engine and other external services requiring authentication.

The following security practices should be followed:

- Authentication credentials should remain on the user's local machine or within the relevant secure authentication mechanism.
- API keys, access tokens, passwords, and private credentials must never be committed to the repository.
- Authentication information must not be embedded in source code.
- Users should not share authentication files publicly.
- Credentials should only be used for their intended services.
- Users should revoke compromised credentials immediately.

## 4. Data Downloads and External Services

GeoToolkit retrieves datasets from third-party services and data providers.

Users should:
- Download data only from supported and trusted sources.
- Verify the origin of downloaded datasets.
- Avoid executing downloaded files or scripts from untrusted sources.
- Keep QGIS, Python dependencies, and the plugin updated.
- Review external service permissions before authenticating.

GeoToolkit cannot guarantee the availability, integrity, or security of external services and datasets.

## 5. Dependencies

GeoToolkit relies on QGIS, Python libraries, and external services.

Dependencies should be maintained and updated where necessary to address known vulnerabilities.

Contributors should avoid introducing unnecessary dependencies and should review third-party packages before incorporating them into the project.

## 6. Repository Security

The project repository should follow these practices:

- Never commit passwords, API keys, or access tokens.
- Exclude local configuration files containing credentials.
- Exclude temporary files and unnecessary generated files.
- Review changes before merging contributions.
- Keep dependencies and development environments updated.
- Use GitHub security features where available.

## 7. Scope

This security policy covers vulnerabilities in:

- GeoToolkit source code.
- Authentication and credential handling implemented by the plugin.
- Download and data-processing mechanisms.
- External service integration.
- Dependencies directly maintained or bundled by the project.

Third-party services and datasets remain subject to their respective providers' security policies.

## 8. Responsible Disclosure

We appreciate responsible security research and the efforts of individuals who help improve GeoToolkit's security.

We aim to investigate valid reports and address confirmed vulnerabilities through appropriate updates.