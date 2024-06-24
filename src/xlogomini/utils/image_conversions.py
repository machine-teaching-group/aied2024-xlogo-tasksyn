import base64
import io
from src.xlogomini.components.code.xlogo_code import Code
from PIL import Image, ImageDraw, ImageFont
from src.xlogomini.utils.enums import *
import os


def text2image(text, show=False, save=True, filename=None):
    # Create a drawing context
    draw = ImageDraw.Draw(Image.new(mode='RGB', size=(1, 1), color=(255, 255, 255)))

    try:
        # local font
        font = ImageFont.truetype(font='Arial.ttf', size=14)
    except:
        # font for remote server
        font = ImageFont.truetype(font="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", size=14)

    width_padding = 30
    height_padding = 30

    text = text.replace('\t', '   ')
    # Get the size of the text
    text_size = draw.textsize(text)

    # Create an image object with the appropriate size
    image_width = min(text_size[0] + width_padding, 500)  # max width is 500
    image_height = min(text_size[1] + height_padding, 500)  # max height is 500
    image = Image.new(mode='RGB', size=(image_width, image_height), color=(255, 255, 255))

    # Create a new drawing context
    draw = ImageDraw.Draw(image)

    # Draw the text on the image
    draw.text((0, 0), text, fill=(0, 0, 0), font=font)

    if show:
        image.show()

    if save:
        image.save(filename, "PNG", quality=50)


def task2image(task_json, show=False, save=True, filename=None, show_desc=False, return_base64=False):
    rows = max([tile['y'] for tile in task_json['tiles']]) + 1
    cols = max([tile['x'] for tile in task_json['tiles']]) + 1
    cell_size = 100

    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../assets/images')

    # Create an empty image
    image = Image.new('RGBA', (cols * (cell_size + 1), rows * (cell_size + 1)), 'white')
    draw = ImageDraw.Draw(image)

    def plot_tiles():
        for tile in task_json['tiles']:
            x = tile['x']
            y = tile['y']

            x0 = x * cell_size
            y0 = y * cell_size

            if 'exist' in tile.keys() and not tile['exist']:
                continue

            if not tile['allowed']:
                draw.rectangle((x0, y0, x0 + cell_size, y0 + cell_size), fill="grey")

            if 'top' in tile['walls'].keys() and tile['walls']['top']:
                draw.line((x0, y0, x0 + cell_size, y0), fill=(0, 0, 0), width=8)
            if 'left' in tile['walls'].keys() and tile['walls']['left']:
                draw.line((x0, y0, x0, y0 + cell_size), fill=(0, 0, 0), width=8)
            if 'right' in tile['walls'].keys() and tile['walls']['right']:
                draw.line((x0 + cell_size, y0, x0 + cell_size, y0 + cell_size), fill=(0, 0, 0), width=8)
            if 'bottom' in tile['walls'].keys() and tile['walls']['bottom']:
                draw.line((x0, y0 + cell_size, x0 + cell_size, y0 + cell_size), fill=(0, 0, 0), width=8)

            draw.line((x0, y0, x0 + cell_size, y0), fill=(0, 0, 0), width=1)
            draw.line((x0, y0, x0, y0 + cell_size), fill=(0, 0, 0), width=1)
            draw.line((x0 + cell_size, y0, x0 + cell_size, y0 + cell_size), fill=(0, 0, 0), width=1)
            draw.line((x0, y0 + cell_size, x0 + cell_size, y0 + cell_size), fill=(0, 0, 0), width=1)

    def plot_turtle():
        turtle = task_json['turtle']
        turtle_img = Image.open(os.path.join(res_path, f"turtle{turtle['direction'] * 90}.png")).convert('RGBA')
        turtle_draw_pos = (int((task_json['turtle']['x'] + 0.5) * cell_size - turtle_img.width / 2),
                           int((task_json['turtle']['y'] + 0.5) * cell_size - turtle_img.height / 2))
        image.paste(turtle_img, turtle_draw_pos, mask=turtle_img)

    def plot_items():
        for item in task_json["items"]:
            x = item["x"]
            y = item["y"]

            if item['name'] == 'strawberry':
                if item['count'] == 1:
                    item_img = Image.open(os.path.join(res_path, "strawberry.png")).convert('RGBA')
                else:
                    item_img = Image.open(os.path.join(res_path, f"{item['count']}strawberry.png")).convert('RGBA')
            elif item['name'] == 'lemon':
                item_img = Image.open(os.path.join(res_path, f"lemon.png")).convert('RGBA')
            elif item['name'] in ITEM_SHAPE:
                item_img = Image.open(os.path.join(res_path, f"{item['name']}-{item['color']}.png")).convert(
                    'RGBA')
            else:
                raise ValueError(f"{item['name']} not recognized!")

            item_draw_pos = (
                int((item["x"] + 0.5) * cell_size - item_img.width // 2),
                int((item["y"] + 0.5) * cell_size - item_img.height // 2),
            )
            image.paste(item_img, item_draw_pos, mask=item_img.split()[3])

    def plot_lines():
        for line in task_json["lines"]:
            # Define line coordinates and color
            x1 = (line['x1'] + 0.5) * cell_size
            y1 = (line['y1'] + 0.5) * cell_size
            x2 = (line['x2'] + 0.5) * cell_size
            y2 = (line['y2'] + 0.5) * cell_size
            color = line['color']
            width = 3
            dash_length = 10  # length of each dash
            dash_gap = 5  # length of gap between dashes

            # Calculate line length and direction
            dx = x2 - x1
            dy = y2 - y1
            line_length = (dx ** 2 + dy ** 2) ** 0.5
            line_direction = (dx / line_length, dy / line_length)

            # Draw line using dashes
            dash_pos = 0
            while dash_pos < line_length:
                # Calculate start and end points of dash
                dash_start = (x1 + line_direction[0] * dash_pos, y1 + line_direction[1] * dash_pos)
                dash_end_pos = dash_pos + dash_length
                if dash_end_pos > line_length:
                    dash_end_pos = line_length
                dash_end = (x1 + line_direction[0] * dash_end_pos, y1 + line_direction[1] * dash_end_pos)

                # Draw dash
                draw.line((dash_start, dash_end), fill=color, width=width)

                # Update dash position
                dash_pos += dash_length + dash_gap

    def plot_task_desc(world_image, text):
        width, height = world_image.size

        # Define padding values
        padding_top = 50
        padding_bottom = 10
        padding_left = 80
        padding_right = 80

        # Increase the font size
        font_size = 20
        max_line_length = 40  # Adjusted for the larger font size

        try:
            # local font
            font = ImageFont.truetype(font='Arial.ttf', size=font_size)
        except:
            # font for remote server
            font = ImageFont.truetype(font="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", size=font_size)

        # Split the text into multiple lines
        lines = []
        line = ''
        for word in text.split():
            if len(line) + len(word) + 1 > max_line_length:
                lines.append(line)
                line = ''
            line += ' ' + word
        lines.append(line)

        # Calculate the total height required for the text
        total_text_height = sum([font.getsize(line)[1] for line in lines]) + 10 * (
                len(lines) - 1)  # 10 pixels padding between lines

        new_width = width + padding_left + padding_right
        new_height = height + total_text_height + 20 + padding_top + padding_bottom  # 20 pixels padding for text

        new_image = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))

        # paste the original image on the new image with padding offsets
        offset_y = padding_top + total_text_height + 20
        offset_x = padding_left
        new_image.paste(world_image, (offset_x, offset_y))

        # add the text above the image
        draw = ImageDraw.Draw(new_image)

        text_y = padding_top + 10  # placing text above the image with extra 10 pixels padding

        for line in lines:
            text_width, text_height = draw.textsize(line, font=font)
            text_x = (new_width - text_width) // 2
            draw.text((text_x, text_y), line.strip(), font=font, fill=(0, 0, 0))
            text_y += text_height + 10  # 10 pixels padding between lines

        return new_image

    def plot_task_desc3(world_image, text):
        width, height = world_image.size

        # Increase the font size
        font_size = 20
        max_line_length = 40  # Adjusted for the larger font size

        try:
            # local font
            font = ImageFont.truetype(font='Arial.ttf', size=font_size)
        except:
            # font for remote server
            font = ImageFont.truetype(font="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", size=font_size)

        # Split the text into multiple lines
        lines = []
        line = ''
        for word in text.split():
            if len(line) + len(word) + 1 > max_line_length:
                lines.append(line)
                line = ''
            line += ' ' + word
        lines.append(line)

        # Calculate the total height required for the text
        total_text_height = sum([font.getsize(line)[1] for line in lines]) + 10 * (
                len(lines) - 1)  # 10 pixels padding between lines

        new_width = width
        new_height = height + total_text_height + 20  # 20 pixels padding

        new_image = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))

        # paste the original image on the new image
        offset_y = (new_height - world_image.height)
        new_image.paste(world_image, (0, offset_y))

        # add the text above the image
        draw = ImageDraw.Draw(new_image)

        text_y = 10  # placing text above the image with extra 10 pixels padding

        for line in lines:
            text_width, text_height = draw.textsize(line, font=font)
            text_x = (new_width - text_width) // 2
            draw.text((text_x, text_y), line.strip(), font=font, fill=(0, 0, 0))
            text_y += text_height + 10  # 10 pixels padding between lines

        return new_image

    plot_tiles()
    plot_items()
    plot_lines()
    plot_turtle()
    if show_desc:
        image = plot_task_desc(world_image=image, text=f"{task_json['description']}")

    if show:
        image.show()

    if save:
        # width, height = image.size
        # image = image.resize((int(width // 1.2), int(height // 1.2)))
        image.save(filename, "PNG", quality=50)

    if return_base64:
        # Convert the image to a base64 encoded string
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return base64_image
    return image


def taskcode2image(task_json, code_text, show=False, save=True, filename=None, return_base64=False):
    # Create the task image using the task2image logic
    task_image = task2image(task_json, show=False, save=False)

    # Convert the code text to an image using the text2image logic
    code_image = text2image(code_text, show=False, save=False)

    # Combine the task and code images
    total_width = max(task_image.width, code_image.width)
    total_height = task_image.height + code_image.height
    combined_image = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))

    # Paste the task and code images onto the combined image
    combined_image.paste(task_image, (0, 0))
    combined_image.paste(code_image, (0, task_image.height))

    # Show, save, or return the combined image based on parameters
    if show:
        combined_image.show()

    if save:
        combined_image.save(filename, "PNG", quality=50)

    # Optionally, return a base64 encoded version of the image
    if return_base64:
        buffer = io.BytesIO()
        combined_image.save(buffer, format='PNG')
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return base64_image
    return combined_image


def add_text_to_image(image_path, text, position='top', font_path='Arial.ttf', font_size=30):
    # Open the image
    image = Image.open(image_path)

    # Create a draw object
    draw = ImageDraw.Draw(image)

    # Load the font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", font_size)

    # Calculate text width and height
    text_width, text_height = draw.textsize(text, font=font)

    if position == 'top':
        # Calculate new image height, add text height plus 10 pixel padding
        new_image_height = image.height + text_height + 10
        # Create new image with extra space at the top
        new_image = Image.new('RGB', (image.width, new_image_height), 'white')
        # Paste the original image onto the new image, shifted down to make space for text
        new_image.paste(image, (0, text_height + 10))
        # Define text position (centered at the top)
        text_x = (image.width - text_width) // 2
        text_y = 10
    elif position == 'bottom':
        # Calculate new image height, add text height plus 20 pixel padding (10 for text, 10 for bottom)
        new_image_height = image.height + text_height + 20
        # Create new image with extra space at the bottom
        new_image = Image.new('RGB', (image.width, new_image_height), 'white')
        # Paste the original image onto the new image
        new_image.paste(image, (0, 0))
        # Define text position (centered at the bottom)
        text_x = (image.width - text_width) // 2
        text_y = image.height + 10
    elif position == 'right':
        # Calculate new image width, add text width plus 30 pixel padding (10 for text, 20 for right)
        new_image_width = image.width + text_width + 30
        # Determine the vertical position of the text to center-align it with the image
        text_y = (image.height - text_height) // 2 if text_height < image.height else 0
        # Create new image with extra space at the right
        new_image = Image.new('RGB', (new_image_width, max(image.height, text_height)), 'white')
        # Paste the original image onto the new image
        new_image.paste(image, (0, (new_image.height - image.height) // 2 if text_height > image.height else 0))
        # Define text position (to the right of the image with 10 pixels padding)
        text_x = image.width + 10
    else:
        raise ValueError("Invalid position. Allowed values are 'top', 'bottom', 'right'.")

    # Redefine the draw object for the new image
    draw = ImageDraw.Draw(new_image)

    # Draw the text on the new image
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return new_image


def add_text_on_top(image_path, text):
    if type(image_path) == str:
        # Open the image
        image = Image.open(image_path)
    else:
        image = image_path

    draw = ImageDraw.Draw(image)

    # Define font and size
    font_size = 30
    try:
        font = ImageFont.truetype('Arial.ttf', font_size)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", font_size)

    # Calculate text width and height
    text_width, text_height = draw.textsize(text, font=font)

    # Define text position (centered)
    text_x = (image.width - text_width) // 2
    text_y = 10  # 10 pixels padding from the top

    # Draw the text on the image
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return image


def add_text_at_bottom(image_path, text):
    if type(image_path) == str:
        # Open the image
        image = Image.open(image_path)
    else:
        image = image_path

    # Create a draw object
    draw = ImageDraw.Draw(image)

    # Define font and size
    font_size = 30
    try:
        font = ImageFont.truetype('Arial.ttf', font_size)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", font_size)

    # Calculate text width and height
    text_width, text_height = draw.textsize(text, font=font)

    # Calculate the new image height with text
    new_image_height = image.height + text_height + 20  # 10 pixels padding below the image

    # Create a new image with extra space at the bottom
    new_image = Image.new('RGB', (image.width, new_image_height), 'white')

    # Paste the original image onto the new image
    new_image.paste(image, (0, 0))

    # Redefine the draw object for the new image
    draw = ImageDraw.Draw(new_image)

    # Define text position (centered and at the new bottom)
    text_x = (new_image.width - text_width) // 2
    text_y = image.height + 10  # 10 pixels below the original image height

    # Draw the text on the new image
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return new_image


def add_text_on_right(image_path, text, font_path='Arial.ttf', font_size=30):
    if type(image_path) == str:
        # Open the image
        image = Image.open(image_path)
    else:
        image = image_path

    # Create a draw object
    draw = ImageDraw.Draw(image)

    # Load the font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", font_size)

    # Calculate text width and height
    text_width, text_height = draw.textsize(text, font=font)

    # Calculate the new image width with text, padding between image and text, and padding at the right
    new_image_width = image.width + text_width + 10 + 20  # Image width + text width + 10 pixels padding + 20 pixels padding at the right

    # Determine the vertical position of the text to center-align it with the image
    if text_height < image.height:
        # Text height is less than image height, so we need to center the text vertically
        text_y = (image.height - text_height) // 2
    else:
        # Text height is greater than image height, so we align the tops and expand the image
        text_y = 0
        new_image_height = text_height
        # Create an expanded image to fit the taller text
        expanded_image = Image.new('RGB', (image.width, new_image_height), 'white')
        expanded_image.paste(image, (0, (new_image_height - image.height) // 2))
        image = expanded_image

    # Create a new image with extra space at the right
    new_image = Image.new('RGB', (new_image_width, image.height), 'white')

    # Paste the original image onto the new image
    new_image.paste(image, (0, 0))

    # Redefine the draw object for the new image
    draw = ImageDraw.Draw(new_image)

    # Define text position (to the right of the image with 10 pixels padding)
    text_x = image.width + 10

    # Draw the text on the new image
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return new_image


def merge_images_horizontal(image1, image2):
    # Determine the dimensions of the new image
    new_width = image1.width + image2.width
    new_height = max(image1.height, image2.height)

    # Create a new image with the determined dimensions
    merged_image = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))

    # Paste the images side by side on the new image
    merged_image.paste(image1, (0, 0))
    merged_image.paste(image2, (image1.width, 0))

    return merged_image


def merge_images_vertical(image1, image2):
    # Determine the dimensions of the new merged image
    new_width = max(image1.width, image2.width)
    new_height = image1.height + image2.height

    # Create a new image with the determined dimensions
    merged_image = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))

    # Calculate horizontal offsets to center each image
    offset_x1 = (new_width - image1.width) // 2
    offset_x2 = (new_width - image2.width) // 2

    # Paste the images top-to-bottom on the new image with the calculated offsets
    merged_image.paste(image1, (offset_x1, 0))
    merged_image.paste(image2, (offset_x2, image1.height))

    return merged_image


def create_task_code_img_sidebyside(syn_task_json, syn_code_json, ref_task_json, ref_code_json, diff=None,
                                    show=False, show_ref=False, save=False, filename=None):
    task_image = task2image(task_json=syn_task_json, show=False, save=False, filename=None, show_desc=True)
    task_code_img = add_text_on_right(task_image, text=str(Code(syn_code_json)))

    if show_ref:
        ref_task_image = task2image(task_json=ref_task_json, show=False, save=False, filename=None, show_desc=True)
        ref_code_img = add_text_on_right(ref_task_image, text=str(Code(ref_code_json)))
        task_code_img = merge_images_horizontal(ref_code_img, task_code_img)
    if diff is not None:
        task_code_img = add_text_at_bottom(task_code_img, text=f"Difficulty: {diff}")
    if show:
        task_code_img.show()
    if save:
        if filename is not None:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            task_code_img.save(filename, quality=50)
            print(f"Image saved to {filename}")
