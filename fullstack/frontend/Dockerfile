FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# TODO: Add command to serve frontend
CMD [-------------------, "--", "--host", "0.0.0.0"]
