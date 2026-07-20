import axios from "axios";

export const getHello = async () => {
  const response = await axios.get(
    "http://127.0.0.1:8000/ecommerceAPP/hello"
  );
  return response.data;
};