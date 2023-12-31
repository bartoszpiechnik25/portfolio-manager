# Portfolio Manager

Purpose of this project is to create a portfolio manager that can be used to track the performance of a portfolio of various financial instruments. The portfolio manager will be able to track the performance of the portfolio over time, provide summary of relevant articles for each stock, index or fund. It will also integrate a simple bot that will answer questions related to financial markets.

## TODO

- :paperclip: Integrate with Google Finance / Yahoo Stock to get stock data and news.
- :framed_picture: Create web interface to display portfolio performance and news.
- :electric_plug: Connect database to web interface.

## Progress

- :white_check_mark: :white_check_mark: :white_check_mark: Fine-tune FLAN-T5 to answer financial questions and generate SQL queries and summarize articles. (see [fine-tuning](./flan_t5/FINE_TUNING.md)).

- ⬜ Dockerize 🐳 LLM and create REST API to serve the model. Progress [=======>.......] 50% - REST API done.

- ⬜ Create a database to store user and portfolio data. Create REST API. Progress: [=======>.....] 60%
