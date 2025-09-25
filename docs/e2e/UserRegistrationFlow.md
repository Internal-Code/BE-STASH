# User Registration Flow

The following diagram shows the registration, OTP verification, and WhatsApp delivery process:

```mermaid
sequenceDiagram
    participant User
    participant Server
    participant DB as Database
    participant OTP as OTP Service
    participant WA as WhatsApp API

    User->>Server: Submit registration data
    Server->>DB: Validate country_id
    Server->>DB: Check phone_number conflict
    Server->>DB: Check email conflict (if provided)
    alt All validations passed
        Server->>DB: Insert user data into Users
        Server->>DB: Insert registration state into UserRegistrationStates
        Server->>DB: Insert otp data into OtpRequests
        Server->>DB: Insert third party data into ThirdPartyServiceHistories
        Server->>OTP: Generate OTP (3 min expiry)
        OTP->>WA: Send OTP message
        WA-->>User: Deliver OTP
    else Validation fails
        Server-->>User: Return error (invalid country / duplicate phone_number / email)
    end

    User->>Server: Submit OTP
    Server->>DB: Ensure OTP already exist
    Server->>DB: Ensure phone number is not yet verified
    Server->>DB: Ensure current time is still within blacklisted otp time
    Server->>DB: Ensure OTP code is equal with user input
    alt OTP valid and not expired
        Server->>DB: Mark phone number as verified
        Server-->>User: Success (phone verified) return user unique id
    else OTP valid but expired
        Server-->>User: Error (OTP expired, request new OTP) return user unique id
    else OTP invalid
        Server-->>User: Error (phone not verified) return user unique id
    end
