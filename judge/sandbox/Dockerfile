FROM python:3.10-slim

# Tạo user không phải root để chạy code untrusted
RUN useradd -m -s /bin/bash botuser

WORKDIR /app

# Đổi sang user thường
USER botuser

# Chờ lệnh stdin/stdout từ runner
CMD ["python", "-u", "student_bot.py"]