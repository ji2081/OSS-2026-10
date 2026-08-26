export function getApiBaseUrl() {
  return (
    process.env.REACT_APP_API_URL ||
    `http://${window.location.hostname}:8000`
  );
}
