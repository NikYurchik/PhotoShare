from typing import List
from typing import Optional

from fastapi import Request

from src.schemas import UserModel, UserModelFix
from src.conf import messages

class UserCreateForm:
    def __init__(self, body: UserModel):
        self.body: UserModel = body
        self.errors: List = []
        self.username: Optional[str] = body.username
        self.email: Optional[str] = body.email
        self.password: Optional[str] = body.password
        self.password2: Optional[str] = body.password2

    async def is_valid(self):
        try:
            user = UserModelFix(username=self.username, email=self.email, password=self.password, password2=self.password2)

            if self.password != self.password2:
                self.errors.append({"key": "password2", "value": messages.PASSWORDS_NOT_MATCH})

        except Exception as err:
            errors = str(err).split("\n")
            errors = errors[1::]        # Удаляем 1-ю строку
            for s in errors:
                if not s.startswith(" "):
                    key = s
                else:
                    s = s.strip()
                    if "For further information visit https://" not in s:
                        i = s.find(" [")
                        value = s[0:i].strip()
                    else:
                        self.errors.append({"key": key, "value": value})

        if not self.errors:
            # print("return True")
            return True
        # print("return False")
        return False

# >>> model_fields: {'username': FieldInfo(annotation=str, required=True, metadata=[MinLen(min_length=4), MaxLen(max_length=16)]), 
#                    'email': FieldInfo(annotation=EmailStr, required=True), 
#                    'password': FieldInfo(annotation=str, required=True, metadata=[MinLen(min_length=6), MaxLen(max_length=12)]), 
#                    'password2': FieldInfo(annotation=str, required=True, metadata=[MinLen(min_length=6), MaxLen(max_length=12)])}

# 2 validation errors for UserModelFix
# username
#   String should have at least 4 characters [type=string_too_short, input_value='te', input_type=str]
#     For further information visit https://errors.pydantic.dev/2.4/v/string_too_short
# password2
#   String should have at least 6 characters [type=string_too_short, input_value='111', input_type=str]
#     For further information visit https://errors.pydantic.dev/2.4/v/string_too_short
