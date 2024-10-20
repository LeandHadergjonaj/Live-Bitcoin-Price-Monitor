import requests
import pandas as pd
import mplfinance as mpf
import matplotlib.backends.backend_agg as agg
import pygame
from pygame.locals import *
import time

# Function to fetch OHLC data from CoinGecko API
def fetch_data(days):
    print(f"Fetching data for last {days} days")
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days={days}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise HTTPError for bad responses
        data = response.json()

        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'Open', 'High', 'Low', 'Close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df['Volume'] = 0  # Placeholder for volume data

        print(f"Fetched {len(df)} rows of data")
        return df
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

# Function to draw graph using mplfinance
def draw_graph(df, plot_type='candle', dark_mode=False):
    if df.empty:
        print("DataFrame is empty, returning empty surface")
        return pygame.Surface((width, height))  # Return an empty surface if no data

    print(f"Drawing graph with {len(df)} rows")
    style = 'nightclouds' if dark_mode else 'charles'
    fig, ax = mpf.plot(df, type=plot_type, style=style, returnfig=True, figsize=(6, 4), warn_too_much_data=100000)
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.buffer_rgba()
    size = canvas.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

# Function to draw buttons
def draw_buttons():
    for label, rect in buttons.items():
        pygame.draw.rect(screen, button_color, rect)
        font = pygame.font.Font(None, 24)
        text = font.render(label, True, text_color)
        screen.blit(text, rect.topleft)

# Function to draw tooltip
def draw_tooltip(x, y, text, dark_mode):
    font = pygame.font.Font(None, 24)
    text_color = (255, 255, 255) if dark_mode else (0, 0, 0)
    text_surface = font.render(text, True, text_color)  # Change text color based on mode
    screen.blit(text_surface, (x, y))

# Initialize Pygame
pygame.init()
infoObject = pygame.display.Info()
width, height = infoObject.current_w, infoObject.current_h
screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
pygame.display.set_caption('Bitcoin Price Chart')

# Define colors
light_mode_bg = (255, 255, 255)
dark_mode_bg = (0, 0, 0)
button_color = (0, 0, 255)  # Blue buttons for contrast
text_color = (255, 255, 255)  # White text for visibility

# Set initial mode
dark_mode = False
background_color = light_mode_bg

# Button definitions
button_width = 80
button_height = 30
button_gap = 10
buttons = {
    '1 Day': pygame.Rect(button_gap, height - button_height - button_gap, button_width, button_height),
    '1 Week': pygame.Rect(button_gap * 2 + button_width, height - button_height - button_gap, button_width, button_height),
    '1 Month': pygame.Rect(button_gap * 3 + button_width * 2, height - button_height - button_gap, button_width, button_height),
    '1 Year': pygame.Rect(button_gap * 4 + button_width * 3, height - button_height - button_gap, button_width, button_height),
    'All Time': pygame.Rect(button_gap * 5 + button_width * 4, height - button_height - button_gap, button_width, button_height),
    'Dark Mode': pygame.Rect(button_gap * 6 + button_width * 5, height - button_height - button_gap, button_width, button_height),
}

# Mapping button labels to the actual number of days
timeframe_map = {
    '1 Day': 1,
    '1 Week': 7,
    '1 Month': 30,
    '1 Year': 365,
    'All Time': 'max',
}

# Cache for data and graphs
data_cache = {}
graph_cache = {}

def get_graph_for_timeframe(label):
    days = timeframe_map.get(label, 1)  # Default to 1 day if label not found
    if label not in data_cache:
        data_cache[label] = fetch_data(days)
    plot_type = 'line' if label == 'All Time' else 'candle'
    if label not in graph_cache or dark_mode_changed:
        graph_cache[label] = draw_graph(data_cache[label], plot_type=plot_type, dark_mode=dark_mode)
    return graph_cache[label]

# Initialize with default timeframe
timeframe_label = '1 Month'
dark_mode_changed = False
graph = get_graph_for_timeframe(timeframe_label)

running = True

while running:
    try:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
            elif event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for label, rect in buttons.items():
                    if rect.collidepoint(pos):
                        if label == 'Dark Mode':
                            dark_mode = not dark_mode
                            dark_mode_changed = True
                            background_color = dark_mode_bg if dark_mode else light_mode_bg
                            graph = get_graph_for_timeframe(timeframe_label)  # Update graph with new mode
                        else:
                            print(f"Button {label} clicked")
                            timeframe_label = label
                            dark_mode_changed = False
                            graph = get_graph_for_timeframe(timeframe_label)

        screen.fill(background_color)

        # Center the graph in the window
        graph_rect = graph.get_rect(center=(width // 2, height // 2 - 50))
        screen.blit(graph, graph_rect.topleft)

        draw_buttons()

        x, y = pygame.mouse.get_pos()
        if 0 < x < width and 0 < y < height - button_height - button_gap and timeframe_label in data_cache and not data_cache[timeframe_label].empty:
            df = data_cache[timeframe_label]
            date_index = min(max(0, x * len(df) // width), len(df) - 1)  # Ensure index is within bounds
            date = df.index[date_index]
            price = df['Close'].iloc[date_index]
            draw_tooltip(x, y, f"{date.strftime('%Y-%m-%d %H:%M')}: ${price:.2f}", dark_mode)

        pygame.display.flip()
        time.sleep(0.1)  # Add a slight delay to reduce CPU usage

    except Exception as e:
        print(f"An error occurred: {e}")
        running = False

pygame.quit()
