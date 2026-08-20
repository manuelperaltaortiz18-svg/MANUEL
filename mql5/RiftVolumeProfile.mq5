//+------------------------------------------------------------------+
//|                                        RiftVolumeProfile.mq5     |
//|  Rift Volume Profile Engine — Expert Advisor para MetaTrader 5    |
//|                                                                  |
//|  Puerto del script de Pine `rift_volume_profile_strategy.pine`.   |
//|  La logica de senales es la misma: perfil de volumen anclado,     |
//|  POC / Value Area / POV, divergencia de CVD, delta de barra y los |
//|  tres modelos (Sweep & Reclaim, POC Bounce, POV Void).            |
//|                                                                  |
//|  DIFERENCIAS QUE IMPORTAN FRENTE A TRADINGVIEW                    |
//|                                                                  |
//|  1. Datos intrabar sin limite de plan. El perfil se construye con |
//|     CopyRates() sobre M1: el alcance del backtest lo marca tu     |
//|     historico descargado, no una cuota.                           |
//|  2. El bracket vive en el servidor del broker. SL y TP se envian  |
//|     junto con la orden, asi que sobreviven a un cierre del        |
//|     terminal o a una caida de conexion. El fallo de Pine —dejar   |
//|     la posicion sin stop porque un nivel valia na— no puede       |
//|     ocurrir aqui.                                                 |
//|  3. Se opera en el CIERRE de vela: el EA actua al abrirse una     |
//|     vela nueva, leyendo la recien cerrada. Entrada a mercado en   |
//|     esa apertura, igual que en el backtest de Pine.               |
//|                                                                  |
//|  ANTES DE USARLO EN REAL                                          |
//|  - Descarga historico M1 del simbolo (Herramientas > Centro de    |
//|    historico) o el backtest no tendra datos con los que trabajar. |
//|  - En el Probador de estrategias usa "Cada tick" u "OHLC M1".     |
//|  - Comprueba el spread real de tu broker: con ratio 1:2 y stops   |
//|    de 1.5 ATR, el coste decide si la ventaja existe.              |
//+------------------------------------------------------------------+
#property copyright "Rift Volume Profile Engine"
#property link      ""
#property version   "1.00"
#property description "Perfil de volumen con POC/VA/POV, divergencia CVD y bracket 1:2"

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Enumeraciones de configuracion                                    |
//+------------------------------------------------------------------+
enum ENUM_ANCHOR_MODE
  {
   ANCHOR_PERIOD,             // Periodo (diario, semanal...)
   ANCHOR_SWING               // Pivotes de swing
  };

enum ENUM_SIGNAL_MODE
  {
   SIGMODE_ALL,               // Todos los modelos
   SIGMODE_SWEEP,             // Sweep & Reclaim
   SIGMODE_BOUNCE,            // POC Bounce
   SIGMODE_VOID               // POV Void
  };

enum ENUM_DIR_MODE
  {
   DIRMODE_BOTH,              // Largos y cortos
   DIRMODE_LONG_ONLY,         // Solo largos
   DIRMODE_SHORT_ONLY         // Solo cortos
  };

enum ENUM_SL_MODE
  {
   SLMODE_ATR_SWEEP,          // ATR mas alla del extremo
   SLMODE_BEYOND_NODE         // Mas alla del nodo de origen
  };

enum ENUM_TP_MODE
  {
   TPMODE_R_MULTIPLE,         // Multiplo de R
   TPMODE_NEXT_NODE           // Siguiente nodo de volumen
  };

enum ENUM_SIZE_MODE
  {
   SIZEMODE_RISK,             // % de riesgo por operacion
   SIZEMODE_FIXED             // Volumen fijo en lotes
  };

//+------------------------------------------------------------------+
//| Entradas                                                          |
//+------------------------------------------------------------------+
input group "=== Motor de perfil de volumen ==="
input ENUM_ANCHOR_MODE  InpAnchor        = ANCHOR_PERIOD;  // Tipo de anclaje del perfil
input int               InpSwingLen      = 10;             // Pivote de swing (velas a cada lado)
input ENUM_TIMEFRAMES   InpAnchorPeriod  = PERIOD_D1;      // Periodo de anclaje
input ENUM_TIMEFRAMES   InpLtf           = PERIOD_M1;      // Feed intrabar
input double            InpTicksPerRow   = 0;              // Ticks por fila (0 = automatico)
input double            InpAtrRows       = 8.0;            // Granularidad automatica (ATR / N)
input double            InpVaPct         = 70.0;           // Value Area objetivo (%)

input group "=== Modelos de senal ==="
input ENUM_SIGNAL_MODE  InpSigMode       = SIGMODE_ALL;    // Modelos activos
input bool              InpRequireDiv    = true;           // Exigir divergencia de CVD
input int               InpDivLen        = 30;             // Ventana de divergencia
input bool              InpRequireDelta  = true;           // Exigir sesgo de delta en la vela
input ENUM_DIR_MODE     InpDirMode       = DIRMODE_BOTH;   // Direccion permitida
input int               InpSigCooldown   = 8;              // Enfriamiento entre senales (velas)

input group "=== Filtros de seguridad ==="
input bool              InpUseMomFilter  = false;          // Filtro de rango (ATR)
input double            InpMomMult       = 2.0;            // Rango maximo (ATR x)
input bool              InpUseWickFilter = false;          // Filtro de mecha de rechazo
input double            InpWickPct       = 30.0;           // Mecha minima (% del rango)
input bool              InpUseEmaFilter  = false;          // Filtro de tendencia EMA
input int               InpEmaLen        = 200;            // Periodo de la EMA
input bool              InpUseSession    = false;          // Filtro de ventana horaria
input int               InpSessStartHour = 8;              // Hora de inicio (hora del servidor)
input int               InpSessEndHour   = 17;             // Hora de fin (hora del servidor)

input group "=== Riesgo y posicion ==="
input ENUM_SL_MODE      InpSlMode        = SLMODE_ATR_SWEEP; // Motor de stop-loss
input ENUM_TP_MODE      InpTpMode        = TPMODE_R_MULTIPLE;// Motor de take-profit
input double            InpSlAtrMult     = 1.5;            // Distancia del stop (ATR x)
input int               InpSlAtrLen      = 14;             // Periodo del ATR del stop
input double            InpRR            = 2.0;            // Ratio objetivo / riesgo
input double            InpNodeBuffer    = 0.25;           // Colchon tras el nodo (ATR x)
input double            InpNodeShare     = 0.5;            // Nodo valido: fraccion del mayor
input double            InpNodeMinRR     = 1.0;            // Nodo valido: R minimo aceptado

input group "=== Ejecucion y cuenta ==="
input ENUM_SIZE_MODE    InpSizeMode      = SIZEMODE_RISK;  // Modo de volumen
input double            InpSizeValue     = 1.0;            // % de riesgo, o lotes fijos
input bool              InpCloseOpposite = true;           // Cerrar la posicion contraria
input int               InpMaxPerDay     = 3;              // Maximo de operaciones por dia
input int               InpMaxLosses     = 3;              // Parar tras N perdidas seguidas
input double            InpDailyLossPct  = 2.0;            // Limite de perdida diaria (%)
input double            InpMaxDdPct      = 0.0;            // Drawdown maximo total (%, 0 = off)
input bool              InpFlatEod       = false;          // Cerrar al acabar la ventana horaria
input int               InpSlippage      = 20;             // Desviacion maxima (puntos)
input ulong             InpMagic         = 20260820;       // Numero magico
input string            InpComment       = "Rift";         // Comentario de las ordenes

input group "=== Visual ==="
input bool              InpDrawLevels    = true;           // Dibujar POC / VAH / VAL / POV
input color             InpColPoc        = clrGold;        // Color del POC
input color             InpColVa         = clrMediumPurple;// Color de la Value Area
input color             InpColVoid       = clrOrange;      // Color del POV

//+------------------------------------------------------------------+
//| Constantes internas                                               |
//+------------------------------------------------------------------+
#define PROFILE_MAX_ROWS 400
#define HIST_SIZE        512     // historico propio de CVD y precios

//+------------------------------------------------------------------+
//| Perfil de volumen: filas de precio con volumen comprador/vendedor |
//+------------------------------------------------------------------+
class CVolumeProfile
  {
public:
   double            m_base;              // precio de la fila 0
   double            m_rowSize;           // altura de cada fila
   double            m_buy[];
   double            m_sell[];
   double            m_tot[];

                     CVolumeProfile(void) : m_base(0.0), m_rowSize(0.0) {}

   void              Reset(const double rowSize, const double refPrice)
     {
      m_rowSize = MathMax(rowSize, SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE));
      if(m_rowSize <= 0.0)
         m_rowSize = _Point;
      m_base = MathFloor(refPrice / m_rowSize) * m_rowSize;
      ArrayResize(m_buy, 0);
      ArrayResize(m_sell, 0);
      ArrayResize(m_tot, 0);
     }

   int               Rows(void) const { return ArraySize(m_tot); }

   int               RowIndex(const double price) const
     {
      if(m_rowSize <= 0.0)
         return 0;
      return (int)MathFloor((price - m_base) / m_rowSize);
     }

   double            RowPrice(const int idx) const
     {
      return m_base + idx * m_rowSize + m_rowSize / 2.0;
     }

   double            Total(void) const
     {
      double sum = 0.0;
      for(int i = 0; i < ArraySize(m_tot); i++)
         sum += m_tot[i];
      return sum;
     }

   double            MaxRow(void) const
     {
      double mx = 0.0;
      for(int i = 0; i < ArraySize(m_tot); i++)
         if(m_tot[i] > mx)
            mx = m_tot[i];
      return mx;
     }

   //--- Crece hacia arriba anadiendo filas al final.
   void              GrowUp(const int targetIdx)
     {
      while(targetIdx > ArraySize(m_tot) - 1 && ArraySize(m_tot) < PROFILE_MAX_ROWS)
        {
         int n = ArraySize(m_tot) + 1;
         ArrayResize(m_buy, n);
         ArrayResize(m_sell, n);
         ArrayResize(m_tot, n);
         m_buy[n - 1]  = 0.0;
         m_sell[n - 1] = 0.0;
         m_tot[n - 1]  = 0.0;
        }
     }

   //--- Crece hacia abajo: inserta filas al principio y baja la base.
   //    Devuelve cuantas filas se han insertado, para corregir indices.
   int               GrowDown(const int negativeIdx)
     {
      int inserted = 0;
      int needed = -negativeIdx;
      while(inserted < needed && ArraySize(m_tot) < PROFILE_MAX_ROWS)
        {
         int n = ArraySize(m_tot) + 1;
         ArrayResize(m_buy, n);
         ArrayResize(m_sell, n);
         ArrayResize(m_tot, n);
         for(int i = n - 1; i > 0; i--)
           {
            m_buy[i]  = m_buy[i - 1];
            m_sell[i] = m_sell[i - 1];
            m_tot[i]  = m_tot[i - 1];
           }
         m_buy[0]  = 0.0;
         m_sell[0] = 0.0;
         m_tot[0]  = 0.0;
         m_base   -= m_rowSize;
         inserted++;
        }
      return inserted;
     }

   void              AddVolume(const int idx, const double volume, const int direction)
     {
      if(idx < 0 || idx >= ArraySize(m_tot))
         return;
      m_tot[idx] += volume;
      if(direction > 0)
         m_buy[idx] += volume;
      else
         if(direction < 0)
            m_sell[idx] += volume;
         else
           {
            m_buy[idx]  += volume / 2.0;
            m_sell[idx] += volume / 2.0;
           }
     }
  };

//+------------------------------------------------------------------+
//| Niveles derivados del perfil                                      |
//+------------------------------------------------------------------+
struct SProfileLevels
  {
   bool              valid;
   double            poc;
   double            vah;
   double            val;
   double            pov;
   int               pocIdx;
   int               povIdx;
  };

//+------------------------------------------------------------------+
//| Estado global                                                     |
//+------------------------------------------------------------------+
CTrade            g_trade;
CVolumeProfile    g_profile;
SProfileLevels    g_levels;

int               g_atrBaseHandle = INVALID_HANDLE;   // ATR(14) para la granularidad
int               g_atrSlHandle   = INVALID_HANDLE;   // ATR del stop
int               g_emaHandle     = INVALID_HANDLE;

datetime          g_lastBarTime   = 0;
datetime          g_profileAnchor = 0;                // inicio del periodo actual
int               g_swingDir      = 0;

double            g_cvd           = 0.0;
double            g_lastLtfClose  = 0.0;               // enlaza el delta entre velas
double            g_cvdHist[HIST_SIZE];               // CVD por vela, indice 0 = mas reciente
double            g_barDelta      = 0.0;
int               g_barsSeen      = 0;

double            g_lastLongNode  = 0.0;
double            g_lastShortNode = 0.0;
int               g_barsSinceLong = 100000;
int               g_barsSinceShort = 100000;

int               g_tradesToday   = 0;
int               g_consecLosses  = 0;
double            g_dayStartEquity = 0.0;
datetime          g_currentDay    = 0;
double            g_peakEquity    = 0.0;
bool              g_accountBlown  = false;
int               g_dealsSeen     = 0;

//+------------------------------------------------------------------+
//| Inicializacion                                                    |
//+------------------------------------------------------------------+
int OnInit(void)
  {
   if(InpRR <= 0.0 || InpSlAtrMult <= 0.0 || InpAtrRows < 2.0)
     {
      Print("Parametros invalidos: revisa RR, ATR multiplicador y granularidad.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(InpSizeMode == SIZEMODE_RISK && InpSizeValue <= 0.0)
     {
      Print("El % de riesgo debe ser mayor que cero.");
      return INIT_PARAMETERS_INCORRECT;
     }

   g_atrBaseHandle = iATR(_Symbol, PERIOD_CURRENT, 14);
   g_atrSlHandle   = iATR(_Symbol, PERIOD_CURRENT, InpSlAtrLen);
   g_emaHandle     = iMA(_Symbol, PERIOD_CURRENT, InpEmaLen, 0, MODE_EMA, PRICE_CLOSE);

   if(g_atrBaseHandle == INVALID_HANDLE || g_atrSlHandle == INVALID_HANDLE ||
      g_emaHandle == INVALID_HANDLE)
     {
      Print("No se pudieron crear los indicadores.");
      return INIT_FAILED;
     }

   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpSlippage);
   g_trade.SetTypeFillingBySymbol(_Symbol);

   ArrayInitialize(g_cvdHist, 0.0);
   g_levels.valid = false;

   // El pico de capital se guarda entre reinicios: una regla de drawdown
   // maximo que se reinicia al recargar el EA no protege de nada.
   string key = "RIFT_PEAK_" + (string)InpMagic + "_" + _Symbol;
   if(GlobalVariableCheck(key))
      g_peakEquity = GlobalVariableGet(key);
   else
      g_peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);

   g_dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_currentDay = DayStart(TimeCurrent());

   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(g_atrBaseHandle != INVALID_HANDLE)
      IndicatorRelease(g_atrBaseHandle);
   if(g_atrSlHandle != INVALID_HANDLE)
      IndicatorRelease(g_atrSlHandle);
   if(g_emaHandle != INVALID_HANDLE)
      IndicatorRelease(g_emaHandle);

   GlobalVariableSet("RIFT_PEAK_" + (string)InpMagic + "_" + _Symbol, g_peakEquity);
   if(InpDrawLevels)
      DeleteLevelObjects();
  }

//+------------------------------------------------------------------+
//| Bucle principal: solo actua al cerrarse una vela                  |
//+------------------------------------------------------------------+
void OnTick(void)
  {
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastBarTime)
      return;                                  // misma vela: nada que hacer
   bool firstRun = (g_lastBarTime == 0);
   g_lastBarTime = barTime;
   if(firstRun)
      return;                                  // no operar con una vela a medio formar

   OnNewBar();
  }

//+------------------------------------------------------------------+
//| Toda la logica, ejecutada una vez por vela cerrada                |
//+------------------------------------------------------------------+
void OnNewBar(void)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int needed = MathMax(InpDivLen + 5, InpSwingLen * 2 + 5);
   if(CopyRates(_Symbol, PERIOD_CURRENT, 0, needed + 5, rates) < needed)
      return;                                  // aun no hay historico suficiente

   // rates[1] es la vela recien cerrada; rates[0] la que acaba de abrirse.
   MqlRates closed = rates[1];

   UpdateAccountState();

   bool newPeriod = DetectNewPeriod(closed, rates);
   if(newPeriod || g_profile.Rows() == 0)
      ResetProfile(closed);

   FeedProfile(closed);
   g_levels = ComputeLevels();

   PushCvd();
   g_barsSeen++;
   g_barsSinceLong++;
   g_barsSinceShort++;

   if(InpDrawLevels)
      DrawLevels();

   if(InpFlatEod && InpUseSession && !InSession(closed.time) && HasPosition())
     {
      ClosePosition("fin de sesion");
      return;
     }
   if(g_accountBlown)
     {
      if(HasPosition())
         ClosePosition("drawdown maximo");
      return;
     }

   EvaluateSignals(closed, rates, newPeriod);
  }

//+------------------------------------------------------------------+
//| Anclaje del perfil                                                |
//+------------------------------------------------------------------+
bool DetectNewPeriod(const MqlRates &closed, const MqlRates &rates[])
  {
   if(InpAnchor == ANCHOR_SWING)
      return DetectSwingFlip(rates);

   datetime anchor = PeriodStart(closed.time, InpAnchorPeriod);
   if(anchor != g_profileAnchor)
     {
      g_profileAnchor = anchor;
      return true;
     }
   return false;
  }

//--- Pivote confirmado: el extremo de hace InpSwingLen velas sigue siendo
//    el mayor (o menor) de su entorno. Equivale a ta.pivothigh/pivotlow.
bool DetectSwingFlip(const MqlRates &rates[])
  {
   int center = 1 + InpSwingLen;
   if(ArraySize(rates) < center + InpSwingLen + 1)
      return false;

   bool isHigh = true, isLow = true;
   double ph = rates[center].high;
   double pl = rates[center].low;
   for(int i = center - InpSwingLen; i <= center + InpSwingLen; i++)
     {
      if(i == center)
         continue;
      if(rates[i].high >= ph)
         isHigh = false;
      if(rates[i].low <= pl)
         isLow = false;
     }

   bool flip = false;
   if(isLow && g_swingDir != 1)
     {
      g_swingDir = 1;
      flip = true;
     }
   if(isHigh && g_swingDir != -1)
     {
      g_swingDir = -1;
      flip = true;
     }
   return flip;
  }

void ResetProfile(const MqlRates &closed)
  {
   double atrBase = IndicatorValue(g_atrBaseHandle, 1);
   double rowSize = InpTicksPerRow > 0.0
                    ? InpTicksPerRow * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE)
                    : (atrBase > 0.0 ? atrBase / InpAtrRows : _Point * 10);
   g_profile.Reset(rowSize, closed.open);
   g_cvd = 0.0;
  }

//+------------------------------------------------------------------+
//| Reparte el volumen intrabar de la vela cerrada entre las filas    |
//+------------------------------------------------------------------+
void FeedProfile(const MqlRates &closed)
  {
   g_barDelta = 0.0;

   datetime from = closed.time;
   datetime to   = closed.time + PeriodSeconds(PERIOD_CURRENT) - 1;

   MqlRates ltf[];
   ArraySetAsSeries(ltf, false);
   int count = CopyRates(_Symbol, InpLtf, from, to, ltf);
   if(count <= 0)
     {
      // Sin datos intrabar el perfil no se puede construir. Se avisa una vez
      // por sesion en vez de operar con un perfil vacio.
      static datetime warned = 0;
      if(warned != g_currentDay)
        {
         warned = g_currentDay;
         PrintFormat("Sin datos %s para %s: descarga el historico intrabar.",
                     EnumToString(InpLtf), _Symbol);
        }
      return;
     }

   for(int i = 0; i < count; i++)
     {
      double vol = (double)ltf[i].tick_volume;
      if(ltf[i].real_volume > 0)
         vol = (double)ltf[i].real_volume;
      if(vol <= 0.0)
         continue;

      // Direccion como en Pine: signo del cambio de cierre entre subvelas.
      // La primera subvela se compara con el ultimo cierre de la vela anterior;
      // si se dejara a cero, se perderia el delta de 1 de cada N subvelas.
      double prevClose = (i > 0) ? ltf[i - 1].close : g_lastLtfClose;
      int dir = 0;
      if(prevClose > 0.0)
        {
         if(ltf[i].close > prevClose)
            dir = 1;
         else
            if(ltf[i].close < prevClose)
               dir = -1;
        }
      g_barDelta += vol * dir;

      int r0 = g_profile.RowIndex(ltf[i].low);
      int r1 = g_profile.RowIndex(ltf[i].high);

      if(r0 < 0)
        {
         int shifted = g_profile.GrowDown(r0);
         r0 += shifted;
         r1 += shifted;
        }
      g_profile.GrowUp(r1);

      r0 = MathMax(r0, 0);
      r1 = MathMin(r1, g_profile.Rows() - 1);
      if(r0 > r1)
         continue;

      double per = vol / (double)(r1 - r0 + 1);
      for(int x = r0; x <= r1; x++)
         g_profile.AddVolume(x, per, dir);
     }

   g_lastLtfClose = ltf[count - 1].close;
   g_cvd += g_barDelta;
  }

//+------------------------------------------------------------------+
//| POC, Value Area y Point of Void                                   |
//+------------------------------------------------------------------+
SProfileLevels ComputeLevels(void)
  {
   SProfileLevels out;
   out.valid  = false;
   out.poc    = 0.0;
   out.vah    = 0.0;
   out.val    = 0.0;
   out.pov    = 0.0;
   out.pocIdx = -1;
   out.povIdx = -1;

   int size = g_profile.Rows();
   double total = g_profile.Total();
   if(size <= 0 || total <= 0.0)
      return out;

   double mx = g_profile.MaxRow();
   int pocIdx = 0;
   for(int i = 0; i < size; i++)
      if(g_profile.m_tot[i] == mx)
        {
         pocIdx = i;
         break;
        }

   double target = total * InpVaPct / 100.0;
   double acc = mx;
   int bt = pocIdx, tp = pocIdx;
   while(acc < target && (bt > 0 || tp < size - 1))
     {
      double up = (tp < size - 1) ? g_profile.m_tot[tp + 1] : -1.0;
      double dn = (bt > 0)        ? g_profile.m_tot[bt - 1] : -1.0;
      if(up >= dn)
        {
         tp++;
         acc += MathMax(up, 0.0);
        }
      else
        {
         bt--;
         acc += MathMax(dn, 0.0);
        }
     }

   out.poc    = g_profile.m_base + pocIdx * g_profile.m_rowSize + g_profile.m_rowSize / 2.0;
   out.vah    = g_profile.m_base + (tp + 1) * g_profile.m_rowSize;
   out.val    = g_profile.m_base + bt * g_profile.m_rowSize;
   out.pocIdx = pocIdx;

   // Point of Void: la fila con menos volumen dentro de la Value Area.
   double minV = 0.0;
   bool haveMin = false;
   for(int x = bt; x <= tp; x++)
     {
      if(x == pocIdx)
         continue;
      double v = g_profile.m_tot[x];
      if(!haveMin || v < minV)
        {
         minV = v;
         haveMin = true;
         out.povIdx = x;
        }
     }
   if(out.povIdx >= 0)
      out.pov = g_profile.RowPrice(out.povIdx);

   out.valid = true;
   return out;
  }

//--- Primer nodo relevante por encima / por debajo de un precio.
double NodeAbove(const double price)
  {
   double mx = g_profile.MaxRow();
   if(mx <= 0.0)
      return 0.0;
   for(int x = 0; x < g_profile.Rows(); x++)
     {
      double lvl = g_profile.RowPrice(x);
      if(lvl > price && g_profile.m_tot[x] >= mx * InpNodeShare)
         return lvl;
     }
   return 0.0;
  }

double NodeBelow(const double price)
  {
   double mx = g_profile.MaxRow();
   if(mx <= 0.0)
      return 0.0;
   for(int x = g_profile.Rows() - 1; x >= 0; x--)
     {
      double lvl = g_profile.RowPrice(x);
      if(lvl < price && g_profile.m_tot[x] >= mx * InpNodeShare)
         return lvl;
     }
   return 0.0;
  }

//+------------------------------------------------------------------+
//| Senales — misma logica que el script de Pine                      |
//+------------------------------------------------------------------+
void EvaluateSignals(const MqlRates &bar, const MqlRates &rates[], const bool newPeriod)
  {
   if(newPeriod || !g_levels.valid)
      return;

   double atrSl = IndicatorValue(g_atrSlHandle, 1);
   if(atrSl <= 0.0)
      return;

   //--- Modelos
   bool sweepL  = bar.low < g_levels.val && bar.close > g_levels.val && bar.close > bar.open;
   bool sweepS  = bar.high > g_levels.vah && bar.close < g_levels.vah && bar.close < bar.open;
   bool bounceL = bar.low <= g_levels.poc && bar.close > g_levels.poc &&
                  bar.close > bar.open && bar.low > g_levels.val;
   bool bounceS = bar.high >= g_levels.poc && bar.close < g_levels.poc &&
                  bar.close < bar.open && bar.high < g_levels.vah;
   bool voidL = false, voidS = false;
   if(g_levels.povIdx >= 0)
     {
      voidL = bar.close > g_levels.pov && rates[2].close <= g_levels.pov && bar.close > bar.open;
      voidS = bar.close < g_levels.pov && rates[2].close >= g_levels.pov && bar.close < bar.open;
     }

   bool modeSwp = (InpSigMode == SIGMODE_ALL || InpSigMode == SIGMODE_SWEEP);
   bool modeBnc = (InpSigMode == SIGMODE_ALL || InpSigMode == SIGMODE_BOUNCE);
   bool modeVd  = (InpSigMode == SIGMODE_ALL || InpSigMode == SIGMODE_VOID);

   //--- Filtros
   double barRange = bar.high - bar.low;
   bool momOK = !InpUseMomFilter || barRange <= atrSl * InpMomMult;

   double wickL = barRange > 0.0 ? (MathMin(bar.open, bar.close) - bar.low) / barRange * 100.0 : 0.0;
   double wickS = barRange > 0.0 ? (bar.high - MathMax(bar.open, bar.close)) / barRange * 100.0 : 0.0;
   bool wickOkL = !InpUseWickFilter || wickL >= InpWickPct;
   bool wickOkS = !InpUseWickFilter || wickS >= InpWickPct;

   double ema = IndicatorValue(g_emaHandle, 1);
   bool emaOkL = !InpUseEmaFilter || (ema > 0.0 && bar.close > ema);
   bool emaOkS = !InpUseEmaFilter || (ema > 0.0 && bar.close < ema);

   bool sessOK = !InpUseSession || InSession(bar.time);

   bool divOkL = !InpRequireDiv || (bar.low < LowestLow(rates, 2, InpDivLen) &&
                                    g_cvd > LowestCvd(1, InpDivLen));
   bool divOkS = !InpRequireDiv || (bar.high > HighestHigh(rates, 2, InpDivLen) &&
                                    g_cvd < HighestCvd(1, InpDivLen));

   bool deltaOkL = !InpRequireDelta || g_barDelta > 0.0;
   bool deltaOkS = !InpRequireDelta || g_barDelta < 0.0;

   bool rawL = (modeSwp && sweepL && wickOkL) || (modeBnc && bounceL && wickOkL) ||
               (modeVd && voidL);
   bool rawS = (modeSwp && sweepS && wickOkS) || (modeBnc && bounceS && wickOkS) ||
               (modeVd && voidS);

   bool dirOkL = (InpDirMode != DIRMODE_SHORT_ONLY);
   bool dirOkS = (InpDirMode != DIRMODE_LONG_ONLY);

   //--- Nodo de origen, para el stop y para el enfriamiento
   double nodeL = sweepL ? g_levels.val : (bounceL ? g_levels.poc : (voidL ? g_levels.pov : 0.0));
   double nodeS = sweepS ? g_levels.vah : (bounceS ? g_levels.poc : (voidS ? g_levels.pov : 0.0));

   bool dupL = g_barsSinceLong < InpSigCooldown && nodeL > 0.0 && g_lastLongNode > 0.0 &&
               MathAbs(nodeL - g_lastLongNode) < atrSl;
   bool dupS = g_barsSinceShort < InpSigCooldown && nodeS > 0.0 && g_lastShortNode > 0.0 &&
               MathAbs(nodeS - g_lastShortNode) < atrSl;

   bool longSignal  = rawL && divOkL && deltaOkL && momOK && emaOkL && sessOK && dirOkL && !dupL;
   bool shortSignal = rawS && divOkS && deltaOkS && momOK && emaOkS && sessOK && dirOkS && !dupS;

   if(!longSignal && !shortSignal)
      return;

   if(longSignal)
     {
      g_lastLongNode = nodeL;
      g_barsSinceLong = 0;
     }
   if(shortSignal)
     {
      g_lastShortNode = nodeS;
      g_barsSinceShort = 0;
     }

   if(!CanTrade())
      return;

   if(longSignal)
      TryOpen(true, bar, atrSl, nodeL);
   else
      TryOpen(false, bar, atrSl, nodeS);
  }

//+------------------------------------------------------------------+
//| Apertura con stop y objetivo adjuntos                             |
//+------------------------------------------------------------------+
void TryOpen(const bool isLong, const MqlRates &bar, const double atrSl, const double node)
  {
   if(HasPosition())
     {
      bool opposite = (PositionIsLong() != isLong);
      if(!opposite || !InpCloseOpposite)
         return;
      if(!ClosePosition("senal contraria"))
         return;
     }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double entry = isLong ? ask : bid;

   //--- Stop
   double sl;
   if(InpSlMode == SLMODE_BEYOND_NODE && node > 0.0)
      sl = isLong ? MathMin(bar.low, node) - atrSl * InpNodeBuffer
                  : MathMax(bar.high, node) + atrSl * InpNodeBuffer;
   else
      sl = isLong ? bar.low - atrSl * InpSlAtrMult
                  : bar.high + atrSl * InpSlAtrMult;
   sl = NormalizePrice(sl);

   double risk = isLong ? entry - sl : sl - entry;
   if(risk <= 0.0)
      return;                                  // el stop quedaria al otro lado

   //--- Objetivo: multiplo de R, o el siguiente nodo si esta lo bastante lejos
   double tp = isLong ? entry + risk * InpRR : entry - risk * InpRR;
   if(InpTpMode == TPMODE_NEXT_NODE)
     {
      double node2 = isLong ? NodeAbove(entry) : NodeBelow(entry);
      if(node2 > 0.0)
        {
         double distance = isLong ? node2 - entry : entry - node2;
         if(distance >= risk * InpNodeMinRR)
            tp = node2;
        }
     }
   tp = NormalizePrice(tp);

   //--- Distancia minima exigida por el broker
   long stopsLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist = stopsLevel * _Point;
   if(minDist > 0.0 && (MathAbs(entry - sl) < minDist || MathAbs(tp - entry) < minDist))
     {
      PrintFormat("Operacion descartada: stop/objetivo por debajo del minimo del broker (%.1f puntos).",
                  (double)stopsLevel);
      return;
     }

   double lots = CalculateLots(risk);
   if(lots <= 0.0)
     {
      Print("Operacion descartada: el volumen minimo arriesgaria mas del presupuesto.");
      return;
     }

   bool ok = isLong ? g_trade.Buy(lots, _Symbol, 0.0, sl, tp, InpComment)
                    : g_trade.Sell(lots, _Symbol, 0.0, sl, tp, InpComment);
   if(!ok)
     {
      PrintFormat("Orden rechazada: %d %s", g_trade.ResultRetcode(),
                  g_trade.ResultRetcodeDescription());
      return;
     }

   g_tradesToday++;
   PrintFormat("%s %.2f lotes | entrada %.*f | stop %.*f | objetivo %.*f | R:R 1:%.2f",
               isLong ? "COMPRA" : "VENTA", lots, _Digits, entry, _Digits, sl,
               _Digits, tp, MathAbs(tp - entry) / risk);
  }

//+------------------------------------------------------------------+
//| Volumen a partir del riesgo: lo decide el stop, nunca al reves    |
//+------------------------------------------------------------------+
double CalculateLots(const double riskPoints)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0.0)
      step = 0.01;

   double lots;
   if(InpSizeMode == SIZEMODE_FIXED)
      lots = InpSizeValue;
   else
     {
      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      if(tickValue <= 0.0 || tickSize <= 0.0 || riskPoints <= 0.0)
         return 0.0;

      double lossPerLot = (riskPoints / tickSize) * tickValue;
      if(lossPerLot <= 0.0)
         return 0.0;

      double budget = AccountInfoDouble(ACCOUNT_EQUITY) * InpSizeValue / 100.0;
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
      g_tradesToday = 0;
      g_consecLosses = 0;
      g_dayStartEquity = equity;
     }

   if(equity > g_peakEquity)
      g_peakEquity = equity;

   if(InpMaxDdPct > 0.0 && g_peakEquity > 0.0)
      if(equity <= g_peakEquity * (1.0 - InpMaxDdPct / 100.0))
        {
         if(!g_accountBlown)
            PrintFormat("Drawdown maximo alcanzado (%.2f%%). El EA deja de operar.", InpMaxDdPct);
         g_accountBlown = true;
        }

   CountRecentLosses();
  }

//--- Racha de perdidas leida del historial de operaciones cerradas.
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
         break;                                 // la racha se corta en la primera ganadora
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
//| Utilidades de posicion                                            |
//+------------------------------------------------------------------+
bool HasPosition(void)
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

bool PositionIsLong(void)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == (long)InpMagic)
         return PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;
     }
   return false;
  }

bool ClosePosition(const string reason)
  {
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
         return false;
        }
      PrintFormat("Posicion cerrada: %s", reason);
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Utilidades varias                                                 |
//+------------------------------------------------------------------+
double IndicatorValue(const int handle, const int shift)
  {
   double buffer[];
   ArraySetAsSeries(buffer, true);
   if(CopyBuffer(handle, 0, shift, 1, buffer) <= 0)
      return 0.0;
   return buffer[0];
  }

double NormalizePrice(const double price)
  {
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0)
      return NormalizeDouble(price, _Digits);
   return NormalizeDouble(MathRound(price / tickSize) * tickSize, _Digits);
  }

double LowestLow(const MqlRates &rates[], const int startShift, const int count)
  {
   double lowest = DBL_MAX;
   for(int i = startShift; i < startShift + count && i < ArraySize(rates); i++)
      lowest = MathMin(lowest, rates[i].low);
   return lowest == DBL_MAX ? 0.0 : lowest;
  }

double HighestHigh(const MqlRates &rates[], const int startShift, const int count)
  {
   double highest = -DBL_MAX;
   for(int i = startShift; i < startShift + count && i < ArraySize(rates); i++)
      highest = MathMax(highest, rates[i].high);
   return highest == -DBL_MAX ? 0.0 : highest;
  }

//--- El CVD se guarda en un historico propio: no existe como serie nativa.
void PushCvd(void)
  {
   for(int i = HIST_SIZE - 1; i > 0; i--)
      g_cvdHist[i] = g_cvdHist[i - 1];
   g_cvdHist[0] = g_cvd;
  }

double LowestCvd(const int startShift, const int count)
  {
   double lowest = DBL_MAX;
   for(int i = startShift; i < startShift + count && i < HIST_SIZE; i++)
      lowest = MathMin(lowest, g_cvdHist[i]);
   return lowest == DBL_MAX ? 0.0 : lowest;
  }

double HighestCvd(const int startShift, const int count)
  {
   double highest = -DBL_MAX;
   for(int i = startShift; i < startShift + count && i < HIST_SIZE; i++)
      highest = MathMax(highest, g_cvdHist[i]);
   return highest == -DBL_MAX ? 0.0 : highest;
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

datetime PeriodStart(const datetime t, const ENUM_TIMEFRAMES tf)
  {
   int seconds = PeriodSeconds(tf);
   if(seconds <= 0)
      return DayStart(t);
   if(tf == PERIOD_W1 || tf == PERIOD_MN1)
     {
      // Semanal y mensual no encajan en una division entera de segundos.
      MqlDateTime dt;
      TimeToStruct(t, dt);
      dt.hour = 0;
      dt.min = 0;
      dt.sec = 0;
      if(tf == PERIOD_MN1)
         dt.day = 1;
      else
         return DayStart(t) - dt.day_of_week * 86400;
      return StructToTime(dt);
     }
   return (datetime)((long)t / seconds * seconds);
  }

bool InSession(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   if(InpSessStartHour <= InpSessEndHour)
      return dt.hour >= InpSessStartHour && dt.hour < InpSessEndHour;
   return dt.hour >= InpSessStartHour || dt.hour < InpSessEndHour;   // ventana nocturna
  }

//+------------------------------------------------------------------+
//| Dibujo de niveles                                                 |
//+------------------------------------------------------------------+
void DrawLevels(void)
  {
   if(!g_levels.valid)
      return;
   DrawLine("Rift_POC", g_levels.poc, InpColPoc, 2);
   DrawLine("Rift_VAH", g_levels.vah, InpColVa, 1);
   DrawLine("Rift_VAL", g_levels.val, InpColVa, 1);
   if(g_levels.povIdx >= 0)
      DrawLine("Rift_POV", g_levels.pov, InpColVoid, 1);
  }

void DrawLine(const string name, const double price, const color clr, const int width)
  {
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

void DeleteLevelObjects(void)
  {
   ObjectDelete(0, "Rift_POC");
   ObjectDelete(0, "Rift_VAH");
   ObjectDelete(0, "Rift_VAL");
   ObjectDelete(0, "Rift_POV");
  }
//+------------------------------------------------------------------+
