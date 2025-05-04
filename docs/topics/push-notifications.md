# Remote Agent to Client Updates

<!-- TOC -->

- [Remote Agent to Client Updates](#remote-agent-to-client-updates)
  - [Connected](#connected)
  - [Disconnected](#disconnected)
  - [Setting Task Notifications](#setting-task-notifications)
  - [Agent Security](#agent-security)
  - [Notification Receiver Security](#notification-receiver-security)
      - [Asymmetric keys](#asymmetric-keys)
      - [Symmetric keys](#symmetric-keys)
      - [OAuth](#oauth)
      - [Bearer Token](#bearer-token)
  - [Other Considerations](#other-considerations)
      - [Replay Prevention](#replay-prevention)
      - [Key Rotation](#key-rotation)

<!-- /TOC -->

Some tasks can take more than seconds. They can take minutes, or hours, or even days (_"ship a sample to my client in Florida and notify me when it arrives"_). A2A agents need to communicate over long periods of time. This includes while they are connected and not connected.

Clients can check whether an agent supports streaming and pushNotifications capability in the agent card.

<pre>
{
  "name": "your-agent-name",
  "description": "your-agent-description"
  ...

  "capabilities": {
    <b>"streaming": true,</b>
    <b>"pushNotifications": false,</b>
    "stateTransitionHistory": false
  }

  ...
}
</pre>

The agent can use below methods to get updates about task execution:

1. **Persistent Connection**: Clients can establish a persistent connection with the agent using HTTP + Server-sent events. The agent can then send task updates using those connections per client.

2. **Push Notifications**: Agents can send the latest full Task object payload to client specified push notification URL. This is similar to webhooks on some platforms.

Clients can set notifications for their tasks whether they have subscribed to a Task or not. Agents should send a notification when Agent has processed a task to a stopping state like "completed", "input-required" etc and fully generated state associated message and artifacts.

Clients can set notification info for their tasks whether they have subscribed to a Task or not. Agents should send a notification when Agent sees it appropriate to notify the client. One paradigm could be to send a notification when agent has processed a task to a stopping state like "completed", "input-required" etc and fully generated state associated message and artifacts.

## Connected

While connected, Agents update each other with Task (and related) messages. Clients and Remote Agents can work on multiple tasks concurrently over the same connection.

Clients use [Task/Send](/documentation.md#send-a-task) to update a current task with more information or reply to an agent need. Remote Agents reply with [Task Updates](/documentation.md#streaming-support) while streaming or [Task](/documentation.md#get-a-task) while not streaming. While not streaming, it is acceptable to poll at reasonable intervals.

If the agents become disconnected, they can resume the connection and receive live updates via the [Task/Resubscribe](/documentation.md#resubscribe-to-task) method.

## Disconnected

For disconnected scenarios, A2A supports a push notification mechanism whereby an Agent can notify a Client of an update outside of a connected session via a [PushNotificationConfig](/documentation.md#push-notifications). Within and across enterprises, it is critical that the agent verifies the identity of the notification service, authenticates itself with the service, and presents an identifier that ties the notification to the executing task.

The NotificationService should be considered a separate service from the client agent, and it is not guaranteed or even expected to be the client directly. This NotificationService is responsible for authenticating and authorizing the agent and for proxying the verified notification to the appropriate endpoint (which could be anything from a pub/sub queue, to an email inbox, to another notification service, etc).

For contrived scenarios with isolated client-agent pairs (e.g. local service mesh in a contained VPC, etc.), the client may choose to simply open a port and act as its own NotificationService. However, any enterprise implementation is recommended to have a centralized service that authenticates the remote agents with trusted notification credentials and can handle online/offline scenarios. This can be thought of similarly to a mobile Push Notification Service with its own Authentication and Authorization controls.

## Setting Task Notifications

Clients need to set task push notification config to asynchronously receive task updates. They should generate a taskId and set the push notification configuration for the same using "tasks/pushNotification/set" RPC or directly in the `pushNotification` param of "tasks/send", "tasks/sendSubscribe".

<pre>
interface PushNotificationConfig {
  url: string;
  token?: string; // token unique to this task/session
  authentication?: {
    schemes: string[];
    credentials?: string;
  }
}

interface TaskPushNotificationConfig {
  id: string; //task id
  pushNotificationConfig: PushNotificationConfig;
}

// Request to send to a task (with push notification configuration)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method":"tasks/send",
  "params": {
    "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",    
    "message": {
      "role":"user",
      "parts": [{
        "type":"text",
        "text": "tell me a joke"
      }]   
    },
    "pushNotification": {
      "url": "https://example.com/callback",
      "authentication": {
        "schemes": ["bearer"]
      }
    },
    "metadata": {}
  }
}

//response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",
    "sessionId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed",
    },
    "artifacts": [{
      "name":"joke",
      "parts": [{
          "type":"text",
          "text":"Why did the chicken cross the road? To get to the other side!"
        }]
      }],    
    "metadata": {}
  }
}

// Request to set push notification config
{
  "jsonrpc": "2.0",
  "id": 1,
  "method":"tasks/pushNotification/set",
  "params": {
    "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",    
    "pushNotificationConfig": {
      "url": "https://example.com/callback",
      "authentication": {
        "schemes": ["bearer"]
      }
    }
  }
}

//Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",    
    "pushNotificationConfig": {
      "url": "https://example.com/callback",
      "authentication": {
        "schemes": ["bearer"]
      }
    }
  }
}
</pre>

## Agent Security

Agents should not blindly trust the push notification URL specified by the client. Some commonly used practices are as below:

1. They should verify the push notification URL by issuing a GET challenge request.

   - The challenge request can be the same push notification URL but with a validationToken provided either as a URL query param or a header.
   - The notification service (or the client in simple cases) should respond to challenge request by returning the same validationToken.
   - This seems simple but it helps avoid tricking remote agent into DDoS-ing a URL by a malicious client.
   - Agents can issue this challenge request one-time when the push notification URL is registered or keep checking this URL periodically.
   <pre>
   GET https://abc.com/callback-path?validationToken=randomString
   Content-Length: 0

   HTTP/1.1 200 OK
   Content-Type: text/plain

   randomString
   </pre>

   An example of such check has been added in method `set_push_notification_info` of [LangGraph](https://github.com/google/A2A/blob/main/samples/python/agents/langgraph/task_manager.py) and [CLI Push listener](https://github.com/google/A2A/blob/main/samples/python/hosts/cli/push_notification_listener.py)

2. To further verify the identity of the notification service, it can be asked to sign the above validationToken using a pre-determined secret.
   - The secret could be generated by the agent, specifically for this challenge request.
   - Or if the notification service and agent use a symmetric shared key for authentication, the same key can be used by notification service to sign the validationToken.

## Notification Receiver Security

Notification Receivers should check the authenticity of the notifications they are receiving. A few ways they can do that are described as follows. Also, a collection of ideas for notification security can be found at https://webhooks.fyi

An example of push notifications using JWT + JWKS using asymmetric keys has been added in [LangGraph](https://github.com/google/A2A/blob/main/samples/python/agents/langgraph/__main__.py) and [CLI Host](https://github.com/google/A2A/blob/main/samples/python/hosts/cli/__main__.py)

#### Asymmetric keys

A pair of private and public keys can be generated using ECDSA, RSA etc. These can be generated by the notification server or the remote agent.

1. If the key pair is generated by the notification server, (ex. APNS), the private key needs to be supplied to the agent. The notification server should keep the public key to verify incoming request payloads signed by the agent using the private key.
2. If the key pair is generated by the agent. Then there can be two options:
   - The public key is manually provided to the Notification Receiver.
   - Or the public keys can be provided by the agent through JWKS protocol.

Agents can sign request payload using the private key and provide the request signature as a header. Or they can use JWT protocol to generate a token and provide that as a signature. Benefit of JWT protocol would also be that it standardises common fields like keyId, request timestamp.

#### Symmetric keys

A simpler method can be that both notification server and agents use the same shared key to sign and verify. The notification server verifies the signature by re-signing the payload with the key. Again JWT can be used to generate the signature token.

Asymmetric keys have an advantage as only the agent knows the public key and hence less chances of the key being leaked.

#### OAuth

Agent gets an auth token from OAuth server and supplies that in the push notification request, either as a header or as part of request payload. Notification server extracts the OAuth token and verifies it from the OAuth server.

#### Bearer Token

Either party can generate the bearer token. If generated by the Notification Receiver, it can provide this token to the remote agent through the task push notification configuration.

Since this is part of a request in plain-text, this has a chance of being leaked and hence malicious request payloads can be sent with this token. With asymmetric or symmetric keys, the payload was signed, which allowed Notification Receivers to verify authenticity of request payloads.

## Other Considerations

#### Replay Prevention

Use [`iat` in JWT](https://mojoauth.com/glossary/jwt-issued-at/) or other header to describe the event timestamp. Ideally any event older than 5 mins should be rejected. This provides some protection from replay attacks.
The timestamp should also be part of the overall request data which is fed into calculation of request signature. This validates the authenticity of timestamps as well.

#### Key Rotation

Ideally agents should implement a key rotation with zero downtime. One way to do this is JWKS, it allows agents to publish their public keys, both old and new. Notification Receivers should be able to use both the keys to validate the notification request payload.
