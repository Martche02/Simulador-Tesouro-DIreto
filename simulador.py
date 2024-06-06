import pandas as pd

# Ler o arquivo CSV
file_path = 'Tesouro.csv'
df = pd.read_csv(file_path)

# Convertendo as colunas de data para o formato datetime
df['Data Base'] = pd.to_datetime(df['Data Base'])
df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'])

# Função para obter o primeiro dia de cada mês
def get_first_day_of_month(df):
    return df.groupby([df['Data Base'].dt.year, df['Data Base'].dt.month]).first().reset_index(drop=True)

# Filtrar o dataframe para o primeiro dia de cada mês
df_monthly = get_first_day_of_month(df)

class InvestmentSimulator:
    def __init__(self, initial_amount, df):
        self.df = df
        self.initial_amount = initial_amount
        self.portfolio = {}
        self.cash = initial_amount
        self.current_date = pd.to_datetime('2006-01-01')
        self.historical_prices = {}

    def get_titles_for_month(self, df, date, category):
        month_start = date.replace(day=1)
        month_end = (month_start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        monthly_records = df[(df['Data Base'] >= month_start) & (df['Data Base'] <= month_end) & (df['Tipo Titulo'] == category)]
        
        # Selecionar a entrada mais antiga para cada título na categoria escolhida
        titles = monthly_records.loc[monthly_records.groupby(['Tipo Titulo', 'Data Vencimento'])['Data Base'].idxmin()]
        return titles[['Tipo Titulo', 'Data Vencimento', 'Juros', 'PU Base Manha', 'Data Base']]

    def get_available_titles(self):
        while True:
            category = input("Escolha uma categoria de título: [S]elic, [P]refixado, [I]PCA+, [V]oltar: ").upper()
            if category == 'S':
                category = 'Tesouro Selic'
            elif category == 'P':
                category = 'Tesouro Prefixado'
            elif category == 'I':
                category = 'Tesouro IPCA+'
            elif category == 'V':
                return None  # Retorna None para indicar que o usuário deseja voltar
            else:
                print("Categoria inválida. Escolha novamente.")
                continue
            
            titles = self.get_titles_for_month(self.df, self.current_date, category)
            return titles


    def display_titles_with_index(self, titles):
        print("\nTítulos disponíveis:")
        titles_dict = {}
        for i, (index, row) in enumerate(titles.iterrows(), start=1):
            print(f"[{i}] {row['Tipo Titulo']} {row['Data Vencimento'].strftime('%Y-%m-%d')} - Juros: {row['Juros']} - Preço: {row['PU Base Manha']}")
            titles_dict[i] = (row['Tipo Titulo'], row['Data Vencimento'], row['Data Base'])
        return titles_dict

    def buy(self, title_index, titles_dict, amount):
        if title_index is None:
            return  # Se o usuário escolheu voltar, não faz nada
        title_info = titles_dict[title_index]
        title = f"{title_info[0]}||{title_info[1].strftime('%Y-%m-%d')}"
        
        if self.cash >= amount:
            if title not in self.portfolio:
                self.portfolio[title] = {'amount': amount, 'initial_price': self.get_current_price(title_info[0], title_info[1], title_info[2]), 'initial_date': title_info[2]}
            else:
                self.portfolio[title]['amount'] += amount
            self.cash -= amount


    def sell(self, title_index, titles_dict, percentage):
        title_info = titles_dict[title_index]
        title = f"{title_info[0]}||{title_info[1].strftime('%Y-%m-%d')}"
        
    def sell(self, title_index, titles_dict, percentage):
        if title_index is None:
            return  # Se o usuário escolheu voltar, não faz nada
        title_info = titles_dict[title_index]
        title = f"{title_info[0]}||{title_info[1].strftime('%Y-%m-%d')}"
        
        if title in self.portfolio:
            amount_to_sell = self.portfolio[title]['amount'] * (percentage / 100)
            self.cash += amount_to_sell
            self.portfolio[title]['amount'] -= amount_to_sell
            if self.portfolio[title]['amount'] <= 0:
                del self.portfolio[title]


    def get_statistics(self):
        # Calculando a rentabilidade de cada título e a rentabilidade total
        stats = {'portfolio': {}, 'cash': self.cash, 'total_return_annual': 0}
        total_initial_value = self.initial_amount

        for title, data in self.portfolio.items():
            initial_value = data['amount']
            initial_price = data['initial_price']
            title_parts = title.split('||')
            current_price = self.get_current_price(title_parts[0], pd.to_datetime(title_parts[1]), self.current_date)
            current_value = initial_value * current_price / initial_price

            initial_date = data['initial_date']
            days_held = (self.current_date - initial_date).days
            days_held = 1 if days_held == 0 else days_held
            annual_return = (current_value / initial_value) ** (365 / days_held) - 1

            stats['portfolio'][title] = {
                'initial_value': initial_value,
                'current_value': current_value,
                'annual_return': annual_return
            }

        total_current_value = sum(data['current_value'] for data in stats['portfolio'].values()) + self.cash
        total_days_held = (self.current_date - pd.to_datetime('2006-01-01')).days
        total_days_held = 1 if total_days_held == 0 else total_days_held
        stats['total_return_annual'] = (total_current_value / total_initial_value) ** (365 / total_days_held) - 1

        return stats


    def next_month(self):
        self.current_date += pd.DateOffset(months=1)
        self.update_portfolio()
        #self.available_titles = self.get_available_titles()

    def update_portfolio(self):
        for title in self.portfolio:
            title_parts = title.split('||')
            tipo_titulo = title_parts[0]
            data_vencimento = pd.to_datetime(title_parts[1])
            initial_date = self.portfolio[title]['initial_date']
            current_price = self.get_current_price(tipo_titulo, data_vencimento, self.current_date)
            initial_price = self.portfolio[title]['initial_price']
            self.portfolio[title]['amount'] = self.portfolio[title]['amount'] * (current_price / initial_price)
            self.portfolio[title]['initial_price'] = current_price

    def get_current_price(self, tipo_titulo, data_vencimento, current_date):
        price_record = self.df[(self.df['Tipo Titulo'] == tipo_titulo) & 
                               (self.df['Data Vencimento'] == data_vencimento) & 
                               (self.df['Data Base'] == current_date)]
        if not price_record.empty:
            return price_record['PU Base Manha'].values[0]
        else:
            # Caso o preço não seja encontrado na data atual, manter o último preço conhecido
            last_known_price_record = self.df[(self.df['Tipo Titulo'] == tipo_titulo) & 
                                              (self.df['Data Vencimento'] == data_vencimento) & 
                                              (self.df['Data Base'] < current_date)].sort_values(by='Data Base').iloc[-1]
            return last_known_price_record['PU Base Manha']

def main():
    simulator = InvestmentSimulator(1000, df)

    while True:
        print(f"\nData Atual: {simulator.current_date.strftime('%Y-%m')}")
        action = input("Escolha uma ação: [C]omprar, [V]ender, [E]statísticas, [N]ovo mês, [S]air: ").upper()
        
        if action == 'C':
            available_titles = simulator.get_available_titles()
            if available_titles is None:
                continue  # Usuário escolheu voltar, retorna ao menu principal
            titles_dict = simulator.display_titles_with_index(available_titles)
            while True:
                title_index = input("Escolha um título pelo índice ou [V]oltar: ").upper()
                if title_index == 'V':
                    break  # Usuário escolheu voltar, retorna ao menu principal
                try:
                    title_index = int(title_index)
                    amount = float(input("Quantia para investir: "))
                    simulator.buy(title_index, titles_dict, amount)
                    break  # Sai do loop de compra após uma compra bem-sucedida
                except (ValueError, KeyError):
                    print("Entrada inválida. Tente novamente.")
        
        elif action == 'V':
            stats = simulator.get_statistics()
            print("\nPortfólio Atual:")
            titles_dict = {i: (row.split('||')[0], pd.to_datetime(row.split('||')[1])) for i, row in enumerate(stats['portfolio'].keys(), start=1)}
            for i, title in titles_dict.items():
                a = f"{title[0]}||{title[1].strftime('%Y-%m-%d')}"
                print(f"[{i}] {title[0]} {title[1].strftime('%Y-%m-%d')} - Quantidade: {stats['portfolio'][a]['current_value']}")
            while True:
                title_index = input("Escolha um título para vender pelo índice ou [V]oltar: ").upper()
                if title_index == 'V':
                    break  # Usuário escolheu voltar, retorna ao menu principal
                try:
                    title_index = int(title_index)
                    percentage = float(input("Porcentagem para vender: "))
                    simulator.sell(title_index, titles_dict, percentage)
                    break  # Sai do loop de venda após uma venda bem-sucedida
                except (ValueError, KeyError):
                    print("Entrada inválida. Tente novamente.")
        
        elif action == 'E':
            stats = simulator.get_statistics()
            print("\nEstatísticas do Portfólio:")
            for title, data in stats['portfolio'].items():
                print(f"{title}: Quantidade: {data['initial_value']}")
            print(f"Retorno total anualizado: {stats['total_return_annual']:.2%}")
        
        elif action == 'N':
            simulator.next_month()
            print(f"Avançado para {simulator.current_date.strftime('%Y-%m')}")
        
        elif action == 'S':
            break

if __name__ == "__main__":
    main()
