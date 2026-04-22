# VAD userinfo differences

Compared to the original MAX userinfo, there are several differences in the VAD userinfo. 
First let's begin by looking at an example of the original MAX userinfo.

## Original MAX Userinfo

Originally, MAX used to provide userinfo via the BsnUserInfoService. The most important, and basically only interesting value in that UserInfo response was the user's BSN (social security number).
This BSN was encapsulated in a JWE (JSON Web Encryption) to ensure secure transmission of the sensitive information. To see more details about the original MAX userinfo, checkout the MAX codebase, specifically the `BsnUserInfoService` and the `Userinfo` schema.

## Differences with the VAD Userinfo

When using the VadUserInfoService, the body for the UserInfo response contains different information compared to when the BsnUserInfoService is used. The entire point of the VadUserInfoService is to avoid sharing the user's BSN directly with the client, and instead provide pseudonymized information about the user. To achieve this, the body of the VAD UserInfo response contains the following attributes:

- rid: A reference identifier (single-use token) for retrieving the userinfo
- person's age: The user's age as an integer (to avoid date of birth leakage)
- person's full legal name: The user's full legal name as retrieved from the BRP service
- sub: Subject identifier containing the authentication session ID

For complete type definitions and helper methods, see the [UserInfoDTO](../app/schemas.py).

At first glance, a couple of terms might be unclear. A little explanation of the flow can help clear things up:

- When a user authenticates via VAD, an authentication session is created.
- At the same time, the VAD service is going to contact two different external services to retrieve user information:
  - The BRP service, which provides citizen information such as name and age.
  - The PRS service, which provides a pseudonymized identifier so that the user's social security number (BSN) does not have to be shared directly with the client.

This pseudonym is currently not yet in place, but instead a RID is used. This RID acts as a single use token which can be used to retrieve a pseudonymized identifier from the PRS service.

Therefore, the VAD userinfo contains the following fields:

- `rid`: reference identifier, a single use token that can be used to retrieve the userinfo again
- `person`: a nested object containing personal information about the user, such as their full legal name and age (as int to avoid date of birth leakage)
- `sub`: the subject identifier, which in this case contains the authentication session ID, allowing the client to correlate the userinfo with the authentication session. Later on this will be changed to a pseudonymized identifier from the PRS service

Another big difference, is that currently, the VAD userinfo is not encapsulated in a JWE. This means that the userinfo is not encrypted during transmission. However, the VAD service is expected to be used over secure channels (HTTPS) and the userinfo itself does not contain sensitive information like the BSN. The RID can only be used once and does not reveal any sensitive information on its own. Later on the VAD userinfo will also be encapsulated in a JWE for added security, but during testing and initial rollout phase this is not yet implemented.
