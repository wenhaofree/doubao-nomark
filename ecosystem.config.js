module.exports = {
  apps: [
    {
      name: "doubao-nomark",
      script: "uvicorn",
      args: "app:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
    },
  ],
};
