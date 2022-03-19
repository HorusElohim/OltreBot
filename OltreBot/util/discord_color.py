class DiscordColorMsg:

    @staticmethod
    def red(*args):
        return f'```diff\n- {" ".join(args)}\n```'

    @staticmethod
    def orange(*args):
        return f'```css\n[{" ".join(args)}]\n```'

    @staticmethod
    def yellow(*args):
        return f'```fix\n{" ".join(args)}\n```'

    @staticmethod
    def dark_green(*args):
        return f'```bash\n"{" ".join(args)}"\n```'

    @staticmethod
    def light_green(*args):
        return f'```diff\n+ {" ".join(args)}\n```'

    @staticmethod
    def blue(*args):
        return f'```ini\n[{" ".join(args)}]\n```'
