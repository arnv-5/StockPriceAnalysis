import tkinter as tk
from threading import Thread
import speech_recognition as sr
import yfinance as yf
from forex_python.converter import CurrencyRates
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image, ImageTk
import pyttsx3
import pandas as pd

class StockPriceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Price Checker")
        self.root.geometry("800x600")  # Set the initial size of the window

        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()

        self.create_widgets()

    def create_widgets(self):
        # Stock Symbol Entry
        self.symbol_label = tk.Label(self.root, text="Enter Stock Symbol:")
        self.symbol_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")

        self.symbol_entry = tk.Entry(self.root)
        self.symbol_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Speech Recognition Button
        self.speech_button = tk.Button(self.root, text="Speak", command=self.speech_to_text)
        self.speech_button.grid(row=0, column=2, padx=10, pady=5)

        # Get Stock Price Button
        self.price_button = tk.Button(self.root, text="Get Stock Price", command=self.start_stock_price_thread)
        self.price_button.grid(row=1, column=1, pady=10)

        # Historical Prices Button
        self.historical_button = tk.Button(self.root, text="Get Historical Prices", command=self.start_historical_prices_thread)
        self.historical_button.grid(row=1, column=2, pady=10)

        # Result Display
        self.result_label = tk.Label(self.root, text="")
        self.result_label.grid(row=2, column=0, columnspan=3, pady=10)

        # Stock Price Graph
        self.graph_button = tk.Button(self.root, text="Show Stock Price Graph", command=self.show_stock_price_graph)
        self.graph_button.grid(row=3, column=1, pady=10)

        # Clear Button
        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_entries)
        self.clear_button.grid(row=3, column=2, pady=10)

    def speech_to_text(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            self.speak_text("Please say the stock symbol.")
            print("Please say the stock symbol:")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            self.symbol_entry.delete(0, tk.END)
            self.symbol_entry.insert(0, text)
            print("You said:", text)
        except sr.UnknownValueError:
            print("Sorry, could not understand audio.")
            self.result_label.config(text="Sorry, could not understand audio. Please say the stock symbol again.", fg="red")
            self.speak_text("Sorry, could not understand audio. Please say the stock symbol again.")
        except sr.RequestError as e:
            print(f"Error connecting to Google Speech Recognition service: {e}")

    def speak_text(self, text):
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def get_exchange_rate(self, from_currency, to_currency):
        c = CurrencyRates()
        return c.get_rate(from_currency, to_currency)

    def get_stock_price(self):
        stock_symbol = self.symbol_entry.get()

        if stock_symbol:
            stock = yf.Ticker(stock_symbol)
            current_price = stock.history(period='1d')['Close'].iloc[-1]

            # Get the current exchange rate
            exchange_rate = self.get_exchange_rate('USD', 'INR')

            # Get the company name
            company_name = stock.info['longName']

            # Calculate the price in both dollars and rupees
            price_in_dollars = current_price
            price_in_rupees = current_price * exchange_rate

            result_text = f"Current price for {company_name} ({stock_symbol}): ${price_in_dollars:.2f} (USD) / ₹{price_in_rupees:.2f} (INR)"
            self.result_label.config(text=result_text)
            self.speak_text(result_text)  # Speak the result
        else:
            self.result_label.config(text="Please enter a stock symbol.", fg="red")
            self.speak_text("Please enter a stock symbol.")

    def get_historical_prices(self):
        stock_symbol = self.symbol_entry.get()

        if stock_symbol:
            stock = yf.Ticker(stock_symbol)
            historical_data = stock.history(period='1y')['Close']

            if not historical_data.empty:
                # Convert prices from USD to INR
                c = CurrencyRates()
                conversion_rate = c.get_rate('USD', 'INR')
                historical_data_inr = historical_data * conversion_rate

                # Summarize the historical data for the previous one year
                summarized_data = historical_data_inr.resample('M').mean()

                # Display the summarized data in the table
                table = pd.DataFrame(summarized_data).to_markdown()

                result_text = f"Summarized historical prices for {stock_symbol} (Previous one year):\n{table} (INR)"
                self.result_label.config(text=result_text)
                self.speak_text(f"The summarized historical prices for the previous one year of {stock.info['longName']} are in Rupees.")
            else:
                self.result_label.config(text="Failed to retrieve historical prices.", fg="red")
                self.speak_text("Failed to retrieve historical prices. Please try again.")
        else:
            self.result_label.config(text="Please enter a stock symbol.", fg="red")
            self.speak_text("Please enter a stock symbol.")

    def show_stock_price_graph(self):
        stock_symbol = self.symbol_entry.get()

        if stock_symbol:
            stock = yf.Ticker(stock_symbol)
            historical_data = stock.history(period='1y')['Close']

            if not historical_data.empty:
                # Convert prices from USD to INR
                c = CurrencyRates()
                conversion_rate = c.get_rate('USD', 'INR')
                historical_data_inr = historical_data * conversion_rate

                # Plot the stock prices graph
                plt.figure(figsize=(10, 5))
                plt.plot(historical_data.index, historical_data_inr, label='Stock Price (INR)')
                plt.title(f"Stock Price History for {stock_symbol}")
                plt.xlabel("Date")
                plt.ylabel("Stock Price (INR)")
                plt.legend()
                plt.grid(True)

                # Convert the plot to an image and display it
                buf = BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                img = Image.open(buf)
                img = ImageTk.PhotoImage(img)

                # Create a new window to display the graph
                graph_window = tk.Toplevel(self.root)
                graph_window.title(f"Stock Price History for {stock_symbol}")
                label = tk.Label(graph_window, image=img)
                label.image = img
                label.pack()

            else:
                self.result_label.config(text="Failed to retrieve historical prices.", fg="red")
                self.speak_text("Failed to retrieve historical prices. Please try again.")
        else:
            self.result_label.config(text="Please enter a stock symbol.", fg="red")
            self.speak_text("Please enter a stock symbol.")

    def clear_entries(self):
        self.symbol_entry.delete(0, tk.END)
        self.result_label.config(text="")


    def start_stock_price_thread(self):
        stock_price_thread = Thread(target=self.get_stock_price)
        stock_price_thread.start()

    def start_historical_prices_thread(self):
        historical_prices_thread = Thread(target=self.get_historical_prices)
        historical_prices_thread.start()

# Create the main window
root = tk.Tk()
app = StockPriceGUI(root)

# Start the Tkinter event loop
root.mainloop()
