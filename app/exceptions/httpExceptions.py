from fastapi import HTTPException, status

# 400
used_email_error = HTTPException(status_code=400, detail="Email already registered")

# 401
unauth_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403
permission_denied_error = HTTPException(status_code=403, detail="Permissions denied")

# 404
user_not_found_error = HTTPException(status_code=404, detail="User not found")
expenditure_not_found = HTTPException(status_code=404, detail="Expenditure not found")

# 422
validation_error = HTTPException(status_code=422, detail="Validation error")

# 500
server_error = HTTPException(status_code=500, detail="Something went wrong, please contact administration.")