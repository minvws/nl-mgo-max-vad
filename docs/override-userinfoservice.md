# Override UserinfoService

## Context

The OpenID Connect (OIDC) protocol provides a way for an authentication server
to deliver end-user information in the form of an ID token. In this case, MAX
Core acts as the authentication server. However, instead of implementing its own
logic for gathering and bundling end-user information, MAX Core defines an
interface (`UserinfoService`) and delegates the implementation to the
application built on the MAX Core framework (e.g. the VAD). This way, MAX Core
can support the full OIDC flow without requiring a concrete class capable of
composing the actual end-user info.

## Binding requirement

Even though MAX Core does not come with a `UserinfoService` implementation, it
does enforce a concrete binding of the `UserinfoService` in the DI container,
because it needs to be able to serve an ID token to the relying party.

## VADUserinfoService

The concrete `UserinfoService` implementation used in the VAD is
`VadUserinfoService`. It composes the end-user information out of two sources:
BRP and PRS.

### Diving deeper in the userinfo differences

For a detailed comparison between the original MAX userinfo and the VAD userinfo contents,
please refer to the [VAD userinfo differences](userinfo-differences.md) document. Which emphasizes the differences between the userinfo implementations and explains the structure of the VAD userinfo in detail.
