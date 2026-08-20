//+------------------------------------------------------------------+
//|                                       NasdaqFirstCandle.mq5      |
//|  Cierre fuera del rango de la primera vela — Expert Advisor MT5   |
//|                                                                  |
//|  Puerto de `nasdaq_first_candle_1to1.pine`.                       |
//|                                                                  |
//|  LA REGLA                                                         |
//|    1. La primera vela de la apertura define un rango (max/min).   |
//|    2. La primera vela que CIERRE por encima del maximo -> largo.  |
//|       La primera que cierre por debajo del minimo    -> corto.    |
//|                                                                  |
//|  El disparo es el CIERRE, no el nivel tocado: una vela puede      |
//|  perforar el rango con la mecha y volver dentro, y eso NO es      |
//|  senal. Esa es la diferencia con una ruptura por orden stop.      |
//|                                                                  |
//|  Entrada a MERCADO en la apertura de la vela siguiente. Stop      |
//|  ESTRUCTURAL al otro lado del rango. Objetivo a 1:1 medido desde  |
//|  el precio REAL de llenado, no desde el cierre que confirmo.      |
//|                                                                  |
//|  EL RANGO SE MIDE EN MINUTOS, no en numero de velas: sale igual   |
//|  en M5, M15 o H1, y no se descoloca si falta una vela al abrir.   |
//|                                                                  |
//|  LA HORA: EL FALLO QUE NO DA ERROR                                |
//|  Si la sesion se configura mal, el "rango de la primera vela" se  |
//|  calcula sobre otra hora del dia. No salta ningun aviso: el EA    |
//|  simplemente opera un rango que no es el que quieres.             |
//|                                                                  |
//|  Por eso las horas van en HORA DE NUEVA YORK por defecto y el EA  |
//|  las convierte a hora del servidor usando dos datos que tu sabes: |
//|  el desfase GMT de tu broker en invierno (mira su reloj) y si tu  |
//|  broker cambia de hora en verano (la mayoria europeos, si).       |
//|  El EA imprime la hora resuelta al arrancar y en cada sesion:     |
//|  compruebala contra el grafico una vez y olvidate.                |
//|                                                                  |
//|  Si prefieres poner las horas del servidor a mano, cambia         |
//|  InpTimeRef a "Hora del servidor".                                |
//+------------------------------------------------------------------+
#property copyright "Nasdaq First Candle 1:1"
#property link      ""
#property version   "1.00"
#property description "Cierre fuera del rango de la primera vela, bracket 1:1"

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Enumeraciones                                                     |
//+------------------------------------------------------------------+
enum ENUM_TIME_REF
  {
   TIMEREF_NEW_YORK,          // Hora de Nueva York (se convierte sola)
   TIMEREF_SERVER             // Hora del servidor del broker (tal cual)
  };

enum ENUM_DIRECTION
  {
   DIR_BOTH,                  // Largos y cortos
   DIR_LONG_ONLY,             // Solo largos
   DIR_SHORT_ONLY             // Solo cortos
  };

enum ENUM_LOT_MODE
  {
   LOT_RISK,                  // % de riesgo por operacion
   LOT_FIXED                  // Volumen fijo
  };

//+------------------------------------------------------------------+
//| Entradas                                                          |
//+------------------------------------------------------------------+
input group "=== Sesion ==="
input ENUM_TIME_REF   InpTimeRef       = TIMEREF_NEW_YORK; // Las horas de abajo estan en...
input int             InpSessStartHour = 9;    // Apertura: hora
input int             InpSessStartMin  = 30;   // Apertura: minuto
input int             InpSessEndHour   = 16;   // Cierre de sesion: hora
input int             InpSessEndMin    = 0;    // Cierre de sesion: minuto
input int             InpBrokerGmtOffset = 2;  // Desfase GMT del broker en INVIERNO
input bool            InpBrokerUsesDst = true; // El broker cambia de hora en verano
input int             InpRangeMinutes  = 15;   // Minutos que forman el rango
input int             InpCutoffMinutes = 330;  // Sin entradas tras (min desde apertura)
input int             InpFlatMinutes   = 375;  // Cerrar todo a (min desde apertura)

input group "=== Estrategia ==="
input bool            InpRequireExcursion = false; // Exigir salida y regreso al rango
input double          InpRR            = 1.0;  // Objetivo / Stop (1.0 = 1:1)
input int             InpStopBufTicks  = 2;    // Margen del stop pasado el rango (ticks)
input double          InpMinRangePts   = 0.0;  // Rango minimo (puntos, 0 = sin minimo)
input double          InpMaxRangePts   = 0.0;  // Rango maximo (puntos, 0 = sin tope)
input ENUM_DIRECTION  InpDirection     = DIR_BOTH; // Direcciones permitidas
input int             InpMaxPerDay     = 1;    // Maximo de operaciones por sesion

input group "=== Riesgo y cuenta ==="
input ENUM_LOT_MODE   InpLotMode       = LOT_RISK; // Modo de volumen
input double          InpLotValue      = 0.5;  // % de riesgo, o lotes fijos
input int             InpMaxLosses     = 3;    // Parar tras N perdidas seguidas
input double          InpDailyLossPct  = 2.0;  // Limite de perdida diaria (%)
input double          InpMaxDdPct      = 0.0;  // Drawdown maximo total (%, 0 = off)
input int             InpSlippage      = 20;   // Desviacion maxima (puntos)
input ulong           InpMagic         = 20260821; // Numero magico
input string          InpComment       = "Vela1"; // Comentario de las ordenes

input group "=== Visual ==="
input bool            InpDrawRange     = true; // Dibujar el rango y los niveles
input color           InpColRangeHigh  = clrTeal;      // Color del maximo del rango
input color           InpColRangeLow   = clrOrange;    // Color del minimo del rango
input color           InpColStop       = clrCrimson;   // Color del stop
input color           InpColTarget     = clrLimeGreen; // Color del objetivo

//+------------------------------------------------------------------+
//| Estado                                                            |
//+------------------------------------------------------------------+
CTrade   g_trade;

datetime g_lastBarTime    = 0;
datetime g_sessionOpen    = 0;      // apertura de la sesion en curso
double   g_rangeHigh      = 0.0;
double   g_rangeLow       = 0.0;
bool     g_leftRange      = false;
bool     g_returnedInside = false;

int      g_tradesToday    = 0;
int      g_consecLosses   = 0;
double   g_dayStartEquity = 0.0;
datetime g_currentDay     = 0;
double   g_peakEquity     = 0.0;
bool     g_accountBlown   = false;
int      g_dealsSeen      = 0;

//+------------------------------------------------------------------+
int OnInit(void)
  {
   if(InpRR <= 0.0 || InpRangeMinutes <= 0)
     {
      Print("Parametros invalidos: ratio y minutos de rango deben ser positivos.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(InpCutoffMinutes >= InpFlatMinutes)
      Print("Aviso: el corte de entradas no es anterior al cierre forzado.");
   if(InpLotMode == LOT_RISK && InpLotValue <= 0.0)
     {
      Print("El % de riesgo debe ser mayor que cero.");
      return INIT_PARAMETERS_INCORRECT;
     }

   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpSlippage);
   g_trade.SetTypeFillingBySymbol(_Symbol);

   // El pico de capital sobrevive a reinicios: una regla de drawdown que se
   // reinicia al recargar el EA no protege de nada.
   string key = "VELA1_PEAK_" + (string)InpMagic + "_" + _Symbol;
   g_peakEquity = GlobalVariableCheck(key) ? GlobalVariableGet(key)
                                           : AccountInfoDouble(ACCOUNT_EQUITY);
   g_dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_currentDay = DayStart(TimeCurrent());

   ReportSessionMapping(TimeCurrent());
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   GlobalVariableSet("VELA1_PEAK_" + (string)InpMagic + "_" + _Symbol, g_peakEquity);
   if(InpDrawRange)
      DeleteObjects();
  }

//+------------------------------------------------------------------+
//| Solo se actua al cerrarse una vela                                |
//+------------------------------------------------------------------+
void OnTick(void)
  {
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastBarTime)
      return;
   bool firstRun = (g_lastBarTime == 0);
   g_lastBarTime = barTime;
   if(firstRun)
      return;

   OnNewBar();
  }

//+------------------------------------------------------------------+
void OnNewBar(void)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_CURRENT, 0, 5, rates) < 3)
      return;

   MqlRates bar = rates[1];                    // la vela recien cerrada
   UpdateAccountState();

   datetime openTime;
   bool inSession;
   double minsFromOpen;
   SessionInfo(bar.time, openTime, inSession, minsFromOpen);

   if(!inSession)
     {
      if(HasPosition())
         ClosePosition("fuera de sesion");
      return;
     }

   if(openTime != g_sessionOpen)
      StartSession(openTime);

   double barEndMins = minsFromOpen + PeriodSeconds(PERIOD_CURRENT) / 60.0;

   //--- Construccion del rango: por MINUTOS, no por numero de velas.
   if(minsFromOpen < InpRangeMinutes)
     {
      g_rangeHigh = (g_rangeHigh == 0.0) ? bar.high : MathMax(g_rangeHigh, bar.high);
      g_rangeLow  = (g_rangeLow == 0.0)  ? bar.low  : MathMin(g_rangeLow, bar.low);
      if(InpDrawRange)
         DrawRange();
      return;                                  // la vela del rango nunca opera
     }
   if(g_rangeHigh == 0.0 || g_rangeLow == 0.0)
      return;
   if(InpDrawRange)
      DrawRange();

   //--- Cierre forzado. Se compara el FINAL de la vela: "cerrar a los 375
   //    minutos" es una fecha limite, y en M15 no existe ninguna vela que
   //    empiece exactamente ahi.
   if(barEndMins >= InpFlatMinutes || g_accountBlown)
     {
      if(HasPosition())
         ClosePosition(g_accountBlown ? "drawdown maximo" : "cierre de sesion");
      return;
     }

   //--- Maquina de estados: fuera del rango -> dentro -> fuera otra vez.
   bool closedAbove = bar.close > g_rangeHigh;
   bool closedBelow = bar.close < g_rangeLow;
   bool closedOut   = closedAbove || closedBelow;

   if(!g_leftRange)
     {
      if(closedOut)
         g_leftRange = true;
     }
   else
      if(!g_returnedInside && !closedOut)
         g_returnedInside = true;

   bool armed = InpRequireExcursion ? (g_leftRange && g_returnedInside) : true;
   if(!armed || !closedOut)
      return;

   if(minsFromOpen >= InpCutoffMinutes)
      return;
   if(HasPosition())
      return;                                  // una posicion cada vez
   if(!CanTrade())
      return;

   double rangeSize = g_rangeHigh - g_rangeLow;
   if(rangeSize < InpMinRangePts)
      return;
   if(InpMaxRangePts > 0.0 && rangeSize > InpMaxRangePts)
      return;

   bool goLong = closedAbove && InpDirection != DIR_SHORT_ONLY;
   bool goShort = closedBelow && InpDirection != DIR_LONG_ONLY;
   if(!goLong && !goShort)
      return;

   OpenTrade(goLong);
  }

//+------------------------------------------------------------------+
//| Apertura con stop estructural y objetivo desde el llenado real    |
//+------------------------------------------------------------------+
void OpenTrade(const bool isLong)
  {
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0)
      tickSize = _Point;
   double buffer = InpStopBufTicks * tickSize;

   double sl = isLong ? NormalizePrice(g_rangeLow - buffer)
                      : NormalizePrice(g_rangeHigh + buffer);

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double expected = isLong ? ask : bid;

   double risk = isLong ? expected - sl : sl - expected;
   if(risk <= 0.0)
     {
      Print("Operacion descartada: el precio ya esta al otro lado del stop.");
      return;
     }

   //--- Distancia minima que exige el broker
   long stopsLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist = stopsLevel * _Point;
   if(minDist > 0.0 && risk < minDist)
     {
      PrintFormat("Operacion descartada: el stop (%.1f puntos) queda dentro del "
                  "minimo del broker (%.1f). Ensancharlo romperia el ratio.",
                  risk / _Point, (double)stopsLevel);
      return;
     }

   double lots = CalculateLots(risk);
   if(lots <= 0.0)
     {
      Print("Operacion descartada: el volumen minimo arriesgaria mas del presupuesto.");
      return;
     }

   double tpEstimate = isLong ? NormalizePrice(expected + risk * InpRR)
                              : NormalizePrice(expected - risk * InpRR);

   bool ok = isLong ? g_trade.Buy(lots, _Symbol, 0.0, sl, tpEstimate, InpComment)
                    : g_trade.Sell(lots, _Symbol, 0.0, sl, tpEstimate, InpComment);
   if(!ok)
     {
      PrintFormat("Orden rechazada: %d %s", g_trade.ResultRetcode(),
                  g_trade.ResultRetcodeDescription());
      return;
     }

   g_tradesToday++;
   AlignTargetToFill(isLong, sl);
   VerifyProtection();
  }

//--- El objetivo se mide desde el precio REAL de entrada. El estimado se
//    calculo con ask/bid antes de enviar; si el llenado difiere, el 1:1 se
//    habria quedado en 1:0.9 sin que se notara.
void AlignTargetToFill(const bool isLong, const double sl)
  {
   if(!SelectOwnPosition())
      return;

   double entry = PositionGetDouble(POSITION_PRICE_OPEN);
   double risk = isLong ? entry - sl : sl - entry;
   if(risk <= 0.0)
      return;

   double target = isLong ? NormalizePrice(entry + risk * InpRR)
                          : NormalizePrice(entry - risk * InpRR);
   double current = PositionGetDouble(POSITION_TP);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0)
      tickSize = _Point;

   if(MathAbs(current - target) < tickSize / 2.0)
      return;                                  // ya estaba donde toca

   ulong ticket = PositionGetInteger(POSITION_TICKET);
   if(!g_trade.PositionModify(ticket, sl, target))
      PrintFormat("No se pudo ajustar el objetivo al llenado real: %d",
                  g_trade.ResultRetcode());
   else
      PrintFormat("%s | entrada %.*f | stop %.*f | objetivo %.*f | R:R 1:%.2f",
                  isLong ? "COMPRA" : "VENTA", _Digits, entry, _Digits, sl,
                  _Digits, target, MathAbs(target - entry) / risk);
  }

//--- Red de seguridad: una posicion sin stop en el servidor es justo lo que
//    no puede pasar en una cuenta de prop firm.
void VerifyProtection(void)
  {
   if(!SelectOwnPosition())
      return;
   if(PositionGetDouble(POSITION_SL) != 0.0)
      return;

   Print("ALARMA: la posicion quedo sin stop-loss. Se cierra de inmediato.");
   ClosePosition("sin stop-loss");
  }

//+------------------------------------------------------------------+
//| Sesion                                                            |
//+------------------------------------------------------------------+
//--- Imprime la hora de apertura resuelta. Comprobarla una vez contra el
//    grafico evita el unico fallo de esta estrategia que no da error.
void ReportSessionMapping(const datetime t)
  {
   if(InpTimeRef == TIMEREF_SERVER)
     {
      PrintFormat("Sesion: %02d:%02d-%02d:%02d hora del servidor (sin conversion).",
                  InpSessStartHour, InpSessStartMin, InpSessEndHour, InpSessEndMin);
      return;
     }
   int shift = NewYorkToServerMinutes(t);
   int startM = ((InpSessStartHour * 60 + InpSessStartMin + shift) % 1440 + 1440) % 1440;
   int endM   = ((InpSessEndHour * 60 + InpSessEndMin + shift) % 1440 + 1440) % 1440;
   PrintFormat("Sesion: %02d:%02d-%02d:%02d Nueva York = %02d:%02d-%02d:%02d en el "
               "servidor (desfase %+d min | verano EEUU: %s | verano broker: %s).",
               InpSessStartHour, InpSessStartMin, InpSessEndHour, InpSessEndMin,
               startM / 60, startM % 60, endM / 60, endM % 60, shift,
               IsUsDst(t) ? "si" : "no",
               (InpBrokerUsesDst && IsEuDst(t)) ? "si" : "no");
  }

void StartSession(const datetime openTime)
  {
   ReportSessionMapping(openTime);
   g_sessionOpen    = openTime;
   g_rangeHigh      = 0.0;
   g_rangeLow       = 0.0;
   g_leftRange      = false;
   g_returnedInside = false;
   g_tradesToday    = 0;
  }

//--- Minutos que hay que sumar a una hora de Nueva York para obtener la hora
//    del servidor del broker. Se calcula con datos explicitos, no adivinando.
int NewYorkToServerMinutes(const datetime t)
  {
   int serverOffset = InpBrokerGmtOffset + ((InpBrokerUsesDst && IsEuDst(t)) ? 1 : 0);
   int newYorkOffset = -5 + (IsUsDst(t) ? 1 : 0);
   return (serverOffset - newYorkOffset) * 60;
  }

//--- Devuelve la apertura de la sesion a la que pertenece `t`, si esta dentro.
void SessionInfo(const datetime t, datetime &openTime, bool &inSession, double &minsFromOpen)
  {
   int shift = (InpTimeRef == TIMEREF_NEW_YORK) ? NewYorkToServerMinutes(t) : 0;
   int startM = InpSessStartHour * 60 + InpSessStartMin + shift;
   int endM   = InpSessEndHour * 60 + InpSessEndMin + shift;
   startM = ((startM % 1440) + 1440) % 1440;
   endM   = ((endM % 1440) + 1440) % 1440;

   MqlDateTime dt;
   TimeToStruct(t, dt);
   int nowM = dt.hour * 60 + dt.min;
   datetime day = DayStart(t);

   if(startM < endM)
     {
      inSession = (nowM >= startM && nowM < endM);
      openTime = day + startM * 60;
     }
   else
     {
      // Ventana que cruza medianoche.
      inSession = (nowM >= startM || nowM < endM);
      openTime = (nowM >= startM) ? day + startM * 60 : day - 86400 + startM * 60;
     }
   minsFromOpen = inSession ? (double)(t - openTime) / 60.0 : -1.0;
  }

//--- Horario de verano de EEUU: del segundo domingo de marzo al primero de
//    noviembre. El broker no cambia de hora, pero Nueva York si, asi que la
//    apertura se mueve una hora en el reloj del servidor.
bool IsUsDst(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   if(dt.mon < 3 || dt.mon > 11)
      return false;
   if(dt.mon > 3 && dt.mon < 11)
      return true;

   // Marzo: DST desde el segundo domingo. Noviembre: hasta el primero.
   int firstSundayDay = 1 + ((7 - DayOfWeekFor(dt.year, dt.mon, 1)) % 7);
   if(dt.mon == 3)
      return dt.day >= firstSundayDay + 7;
   return dt.day < firstSundayDay;
  }

//--- Horario de verano europeo: del ultimo domingo de marzo al ultimo de
//    octubre. Lo usan casi todos los brokers con servidor en GMT+2/+3.
bool IsEuDst(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   if(dt.mon < 3 || dt.mon > 10)
      return false;
   if(dt.mon > 3 && dt.mon < 10)
      return true;

   int lastSunday = LastSundayOf(dt.year, dt.mon);
   if(dt.mon == 3)
      return dt.day >= lastSunday;
   return dt.day < lastSunday;
  }

int LastSundayOf(const int year, const int month)
  {
   int days = DaysInMonth(year, month);
   int dow = DayOfWeekFor(year, month, days);
   return days - dow;                          // dow 0 = domingo
  }

int DaysInMonth(const int year, const int month)
  {
   int table[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
   if(month == 2 && ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0))
      return 29;
   return table[month - 1];
  }

int DayOfWeekFor(const int year, const int month, const int day)
  {
   MqlDateTime dt;
   dt.year = year;
   dt.mon = month;
   dt.day = day;
   dt.hour = 12;
   dt.min = 0;
   dt.sec = 0;
   datetime stamp = StructToTime(dt);
   MqlDateTime out;
   TimeToStruct(stamp, out);
   return out.day_of_week;
  }

datetime DayStart(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;
   return StructToTime(dt);
  }

//+------------------------------------------------------------------+
//| Volumen: lo decide el stop, nunca al reves                        |
//+------------------------------------------------------------------+
double CalculateLots(const double riskPoints)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0.0)
      step = 0.01;

   double lots;
   if(InpLotMode == LOT_FIXED)
      lots = InpLotValue;
   else
     {
      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      if(tickValue <= 0.0 || tickSize <= 0.0 || riskPoints <= 0.0)
         return 0.0;
      double lossPerLot = (riskPoints / tickSize) * tickValue;
      if(lossPerLot <= 0.0)
         return 0.0;
      double budget = AccountInfoDouble(ACCOUNT_EQUITY) * InpLotValue / 100.0;
      lots = budget / lossPerLot;
     }

   lots = MathFloor(lots / step) * step;       // hacia abajo: nunca de mas
   lots = MathMin(lots, maxLot);
   if(lots < minLot)
      return 0.0;                              // no se redondea hacia arriba

   int digits = (int)MathMax(0, MathRound(-MathLog10(step)));
   return NormalizeDouble(lots, digits);
  }

//+------------------------------------------------------------------+
//| Cortacircuitos de cuenta                                          |
//+------------------------------------------------------------------+
void UpdateAccountState(void)
  {
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   datetime today = DayStart(TimeCurrent());
   if(today != g_currentDay)
     {
      g_currentDay = today;
      g_consecLosses = 0;
      g_dayStartEquity = equity;
     }

   if(equity > g_peakEquity)
      g_peakEquity = equity;

   if(InpMaxDdPct > 0.0 && g_peakEquity > 0.0)
      if(equity <= g_peakEquity * (1.0 - InpMaxDdPct / 100.0))
        {
         if(!g_accountBlown)
            PrintFormat("Drawdown maximo alcanzado (%.2f%%). El EA deja de operar.",
                        InpMaxDdPct);
         g_accountBlown = true;
        }

   CountRecentLosses();
  }

void CountRecentLosses(void)
  {
   if(!HistorySelect(g_currentDay, TimeCurrent()))
      return;
   int total = HistoryDealsTotal();
   if(total == g_dealsSeen)
      return;
   g_dealsSeen = total;

   int streak = 0;
   for(int i = total - 1; i >= 0; i--)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != (long)InpMagic)
         continue;
      if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;
      double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT) +
                      HistoryDealGetDouble(ticket, DEAL_SWAP) +
                      HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      if(profit < 0.0)
         streak++;
      else
         break;                                 // la racha se corta con una ganadora
     }
   g_consecLosses = streak;
  }

bool CanTrade(void)
  {
   if(g_accountBlown)
      return false;
   if(g_tradesToday >= InpMaxPerDay)
      return false;
   if(g_consecLosses >= InpMaxLosses)
      return false;
   if(InpDailyLossPct > 0.0 && g_dayStartEquity > 0.0)
     {
      double dayPnl = AccountInfoDouble(ACCOUNT_EQUITY) - g_dayStartEquity;
      if(dayPnl <= -g_dayStartEquity * InpDailyLossPct / 100.0)
         return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Posiciones                                                        |
//+------------------------------------------------------------------+
bool SelectOwnPosition(void)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == (long)InpMagic)
         return true;
     }
   return false;
  }

bool HasPosition(void)
  {
   return SelectOwnPosition();
  }

bool ClosePosition(const string reason)
  {
   bool allClosed = true;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagic)
         continue;
      if(!g_trade.PositionClose(ticket, InpSlippage))
        {
         PrintFormat("No se pudo cerrar (%s): %d", reason, g_trade.ResultRetcode());
         allClosed = false;
        }
      else
         PrintFormat("Posicion cerrada: %s", reason);
     }
   return allClosed;
  }

//+------------------------------------------------------------------+
//| Utilidades y dibujo                                               |
//+------------------------------------------------------------------+
double NormalizePrice(const double price)
  {
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0)
      return NormalizeDouble(price, _Digits);
   return NormalizeDouble(MathRound(price / tickSize) * tickSize, _Digits);
  }

void DrawRange(void)
  {
   if(g_rangeHigh == 0.0 || g_rangeLow == 0.0)
      return;
   DrawLine("Vela1_High", g_rangeHigh, InpColRangeHigh, 2);
   DrawLine("Vela1_Low", g_rangeLow, InpColRangeLow, 2);

   if(SelectOwnPosition())
     {
      DrawLine("Vela1_SL", PositionGetDouble(POSITION_SL), InpColStop, 2);
      DrawLine("Vela1_TP", PositionGetDouble(POSITION_TP), InpColTarget, 2);
     }
   else
     {
      ObjectDelete(0, "Vela1_SL");
      ObjectDelete(0, "Vela1_TP");
     }
  }

void DrawLine(const string name, const double price, const color clr, const int width)
  {
   if(price <= 0.0)
      return;
   if(ObjectFind(0, name) < 0)
     {
      ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
     }
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
  }

void DeleteObjects(void)
  {
   ObjectDelete(0, "Vela1_High");
   ObjectDelete(0, "Vela1_Low");
   ObjectDelete(0, "Vela1_SL");
   ObjectDelete(0, "Vela1_TP");
  }
//+------------------------------------------------------------------+
