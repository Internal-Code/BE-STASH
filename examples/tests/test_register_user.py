import httpx
import pytest
from faker import Faker
from src.auth.utils.generator import random_number
from src.auth.utils.database.general import extract_data_otp, check_fullname

faker = Faker()


@pytest.mark.asyncio
async def test_create_user_with_valid_data() -> None:
    """
    Should sucessfully register new user.
    """

    full_name = await check_fullname(value=faker.name())
    data = {"full_name": full_name, "phone_number": str(await random_number(10))}

    async with httpx.AsyncClient() as client:
        regis_user = await client.post(
            "http://localhost:8000/api/v1/users/register", json=data
        )
        print(regis_user.content)
        response = regis_user.json()
        assert regis_user.status_code == 201

        user_uuid = response["data"]["unique_id"]

        send_otp = await client.post(
            f"http://localhost:8000/api/v1/send-otp/phone-number/{user_uuid}",
            params=user_uuid,
        )
        print(send_otp.content)
        assert send_otp.status_code == 200

        otp_code = await extract_data_otp(user_uuid=user_uuid)

        otp_data = {"otp": otp_code.otp_number}
        verify_otp = await client.post(
            f"http://localhost:8000/api/v1/verify/phone-number/{user_uuid}",
            json=otp_data,
            params=user_uuid,
        )
        print(verify_otp.content)
        assert verify_otp.status_code == 200

        pin_data = {"pin": str(111111)}

        create_pin = await client.patch(
            f"http://localhost:8000/api/v1/users/create-pin/{user_uuid}",
            json=pin_data,
            params=user_uuid,
        )
        assert create_pin.status_code == 201
